from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.orders import parse_money
from app.models.audit import AuditEvent, AuditEventType
from app.models.business_entities import Order
from app.models.conversation import Conversation, Message, MessageSender
from app.models.refund import RefundExecution
from app.models.workflow import (
    ActionProposal,
    OutcomeEvidence,
    ProposalStatus,
    Task,
    TaskStatus,
)


class ProofOfOutcomeEngine:
    """Verify local refund receipts against the current order ledger."""

    def verify_task_outcome(
        self,
        db: Session,
        organization_id: str,
        task_id: str,
        actor_id: str = "engine:proof_of_outcome",
    ) -> tuple[bool, str, dict[str, Any]]:
        task = (
            db.query(Task)
            .filter(
                Task.id == task_id,
                Task.organization_id == organization_id,
            )
            .with_for_update()
            .first()
        )

        if task is None:
            return False, "Task not found.", {}

        proposals = (
            db.query(ActionProposal)
            .filter(
                ActionProposal.task_id == task.id,
                ActionProposal.organization_id == organization_id,
                ActionProposal.status == ProposalStatus.EXECUTED,
            )
            .all()
        )

        if len(proposals) != 1:
            return (
                False,
                "Verification requires exactly one executed action for this task.",
                {},
            )

        proposal = proposals[0]

        if proposal.action_type != "stripe_partial_refund":
            return False, "This action has no supported outcome verifier.", {}

        if not proposal.target_entity.startswith("order:"):
            return False, "The executed action has an invalid order target.", {}

        payload = proposal.payload

        if not isinstance(payload, dict):
            return False, "The executed action has an invalid payload.", {}

        try:
            expected_amount = parse_money(payload.get("amount"))
        except ValueError:
            return False, "The executed action has an invalid amount.", {}

        order_number = proposal.target_entity.removeprefix("order:")

        receipt = (
            db.query(RefundExecution)
            .filter(
                RefundExecution.organization_id == organization_id,
                RefundExecution.idempotency_key == proposal.idempotency_key,
            )
            .first()
        )

        if receipt is None:
            return (
                False,
                "No execution receipt exists. Do not retry the refund blindly.",
                {},
            )

        order = (
            db.query(Order)
            .filter(
                Order.id == receipt.order_id,
                Order.organization_id == organization_id,
            )
            .with_for_update()
            .first()
        )

        if order is None:
            return False, "The receipt's order could not be retrieved.", {}

        try:
            current_refunded = Decimal(str(order.refunded_amount))
            order_total = Decimal(str(order.total_amount))
        except (InvalidOperation, ValueError, TypeError):
            return False, "The order contains an invalid financial balance.", {}

        if not current_refunded.is_finite() or not order_total.is_finite():
            return False, "The order contains a non-finite balance.", {}

        checks = {
            "order_reference_matches": order.order_number == order_number,
            "customer_matches": order.customer_id == task.customer_id,
            "amount_matches": receipt.amount == expected_amount,
            "currency_matches": (
                receipt.currency == order.currency
                and payload.get("currency") == order.currency
            ),
            "reason_matches": receipt.reason == payload.get("reason"),
            "receipt_delta_matches": (
                receipt.resulting_refunded_amount
                - receipt.previous_refunded_amount
                == expected_amount
            ),
            "receipt_balance_valid": (
                Decimal("0.00")
                <= receipt.previous_refunded_amount
                < receipt.resulting_refunded_amount
                <= order_total
            ),
            "current_balance_contains_refund": (
                receipt.resulting_refunded_amount
                <= current_refunded
                <= order_total
            ),
        }

        is_verified = all(checks.values())
        failed_checks = [
            name for name, passed in checks.items() if not passed
        ]

        expected_outcome = {
            "action_proposal_id": proposal.id,
            "order_number": order_number,
            "refund_amount": str(expected_amount),
            "currency": payload.get("currency"),
            "idempotency_key": proposal.idempotency_key,
        }

        actual_outcome = {
            "execution_id": receipt.id,
            "order_number": order.order_number,
            "receipt_amount": str(receipt.amount),
            "previous_refunded_amount": str(
                receipt.previous_refunded_amount
            ),
            "resulting_refunded_amount": str(
                receipt.resulting_refunded_amount
            ),
            "current_refunded_amount": str(current_refunded),
            "order_total": str(order_total),
            "currency": order.currency,
            "checks": checks,
            "system": "local_demonstration_ledger",
        }

        summary = (
            f"Verified local refund of {expected_amount} "
            f"{receipt.currency} for order {order_number}."
            if is_verified
            else "Verification failed: " + ", ".join(failed_checks)
        )

        evidence = (
            db.query(OutcomeEvidence)
            .filter(
                OutcomeEvidence.task_id == task.id,
                OutcomeEvidence.organization_id == organization_id,
            )
            .first()
        )

        previously_verified = bool(
            evidence is not None
            and evidence.is_verified
            and task.status == TaskStatus.VERIFIED
        )

        if evidence is None:
            evidence = OutcomeEvidence(
                organization_id=organization_id,
                task_id=task.id,
            )
            db.add(evidence)

        evidence.expected_outcome = expected_outcome
        evidence.actual_outcome = actual_outcome
        evidence.is_verified = is_verified
        evidence.evidence_summary = summary

        if is_verified:
            if evidence.verified_at is None or not previously_verified:
                evidence.verified_at = datetime.utcnow()
        else:
            evidence.verified_at = None

        task.status = (
            TaskStatus.VERIFIED if is_verified else TaskStatus.FAILED
        )

        # Allocate the evidence ID before referring to it in other records.
        db.flush()

        if is_verified and not previously_verified:
            db.add(
                AuditEvent(
                    organization_id=organization_id,
                    event_type=AuditEventType.OUTCOME_VERIFIED,
                    actor_id=actor_id,
                    target_id=task.id,
                    summary=summary[:255],
                    details={
                        "evidence_id": evidence.id,
                        "execution_id": receipt.id,
                        "checks": checks,
                    },
                    idempotency_key=proposal.idempotency_key,
                )
            )

            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.task_id == task.id,
                    Conversation.organization_id == organization_id,
                    Conversation.customer_id == task.customer_id,
                )
                .first()
            )

            if conversation is not None:
                db.add(
                    Message(
                        organization_id=organization_id,
                        conversation_id=conversation.id,
                        sender=MessageSender.SYSTEM,
                        content=(
                            f"Local demonstration refund verified: "
                            f"{expected_amount} {receipt.currency} "
                            f"for order {order_number}. "
                            f"Evidence: {evidence.id}."
                        ),
                    )
                )

        elif not is_verified:
            db.add(
                AuditEvent(
                    organization_id=organization_id,
                    event_type=AuditEventType.SECURITY_VIOLATION,
                    actor_id=actor_id,
                    target_id=task.id,
                    summary="Refund outcome verification failed.",
                    details={
                        "evidence_id": evidence.id,
                        "failed_checks": failed_checks,
                    },
                )
            )

        db.commit()

        return is_verified, summary, {
            "task_id": task.id,
            "status": task.status.value,
            "is_verified": is_verified,
            "evidence_id": evidence.id,
            "expected": expected_outcome,
            "actual": actual_outcome,
        }

    def recover_failed_task(
        self,
        db: Session,
        organization_id: str,
        task_id: str,
        actor_id: str = "engine:recovery",
    ) -> tuple[bool, str, dict[str, Any]]:
        """Retry verification without issuing another refund."""

        task = (
            db.query(Task)
            .filter(
                Task.id == task_id,
                Task.organization_id == organization_id,
            )
            .first()
        )

        if task is None:
            return False, "Task not found.", {}

        if task.status == TaskStatus.VERIFIED:
            return False, "This task is already verified.", {}

        if task.status not in {
            TaskStatus.EXECUTING,
            TaskStatus.VERIFYING,
            TaskStatus.FAILED,
        }:
            return (
                False,
                "Task is not awaiting verification recovery.",
                {},
            )

        return self.verify_task_outcome(
            db=db,
            organization_id=organization_id,
            task_id=task_id,
            actor_id=actor_id,
        )


outcome_engine = ProofOfOutcomeEngine()