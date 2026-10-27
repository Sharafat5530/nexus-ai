from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.orders import order_adapter, parse_money
from app.models.audit import AuditEvent, AuditEventType
from app.models.business_entities import Order
from app.models.execution_control import ExecutionControl
from app.models.refund import RefundExecution
from app.models.tenant import User, UserRole
from app.models.workflow import (
    ApprovalStatus,
    ActionProposal,
    ProposalStatus,
    TaskStatus,
)


class DeterministicActionGateway:
    ALLOWED_ACTIONS = {"stripe_partial_refund"}
    MAX_REFUND_LIMIT = Decimal("50.00")

    @staticmethod
    def reject(
        db: Session,
        organization_id: str,
        proposal_id: str,
        actor_id: str,
        message: str,
    ) -> tuple[bool, str, dict[str, Any]]:
        db.add(
            AuditEvent(
                organization_id=organization_id,
                event_type=AuditEventType.ACTION_BLOCKED,
                actor_id=actor_id,
                target_id=proposal_id,
                summary=message[:255],
                details={"source": "action_gateway"},
            )
        )
        return False, message, {}

    def evaluate_and_execute(
        self,
        db: Session,
        organization_id: str,
        proposal_id: str,
        actor_id: str,
    ) -> tuple[bool, str, dict[str, Any]]:
        proposal = (
            db.query(ActionProposal)
            .filter(
                ActionProposal.id == proposal_id,
                ActionProposal.organization_id == organization_id,
            )
            .with_for_update()
            .first()
        )

        if proposal is None:
            return False, "Proposal not found.", {}

        def deny(message: str):
            return self.reject(
                db,
                organization_id,
                proposal_id,
                actor_id,
                message,
            )

        task = proposal.task

        if task is None or task.organization_id != organization_id:
            return deny("Proposal has no valid task in this organization.")

        if proposal.action_type not in self.ALLOWED_ACTIONS:
            return deny("This action is not supported by the gateway.")

        if not proposal.target_entity.startswith("order:"):
            return deny("A refund must target an order.")

        order_number = proposal.target_entity.removeprefix("order:")

        if not order_number:
            return deny("The order reference is missing.")

        payload = proposal.payload

        if not isinstance(payload, dict):
            return deny("The proposal payload is invalid.")

        amount = parse_money(payload.get("amount"))
        reason = payload.get("reason")

        if not isinstance(reason, str) or not reason.strip():
            return deny("A refund reason is required.")

        if len(reason) > 255:
            return deny("The refund reason exceeds 255 characters.")

        if amount > self.MAX_REFUND_LIMIT:
            return deny("Refund exceeds the gateway limit of 50.00.")

        order = (
            db.query(Order)
            .filter(
                Order.organization_id == organization_id,
                Order.order_number == order_number,
            )
            .first()
        )

        if order is None:
            return deny("Order not found in this organization.")

        if payload.get("currency") != order.currency:
            return deny("Refund currency must match the order currency.")

        if task.customer_id != order.customer_id:
            return deny("The order does not belong to the task customer.")

        if proposal.status == ProposalStatus.EXECUTED:
            receipt = (
                db.query(RefundExecution)
                .filter(
                    RefundExecution.organization_id == organization_id,
                    RefundExecution.idempotency_key == proposal.idempotency_key,
                )
                .first()
            )

            if receipt is None:
                return deny("Executed proposal has no refund receipt.")

            if (
                receipt.order_id != order.id
                or receipt.amount != amount
                or receipt.currency != order.currency
                or receipt.reason != reason
            ):
                return deny("Execution receipt does not match the proposal.")

            return (
                True,
                "This action was already executed.",
                order_adapter.build_receipt(
                    receipt,
                    order_number,
                    repeated=True,
                ),
            )

        control = db.get(ExecutionControl, "global")

        if control is not None and control.paused:
            return deny("Execution is paused by an administrator.")

        if proposal.status != ProposalStatus.APPROVED:
            return deny("The proposal must be approved before execution.")

        approval = proposal.approval

        if (
            approval is None
            or approval.organization_id != organization_id
            or approval.status != ApprovalStatus.APPROVED
        ):
            return deny("A valid human approval is required.")

        if (
            approval.expires_at is None
            or approval.expires_at <= datetime.utcnow()
        ):
            return deny("Approval has expired or has no expiry time.")

        reviewer = (
            db.query(User)
            .filter(
                User.id == approval.reviewer_id,
                User.organization_id == organization_id,
                User.is_active.is_(True),
                User.role.in_(
                    [UserRole.ADMIN, UserRole.AGENT_OPERATOR]
                ),
            )
            .first()
        )

        if reviewer is None:
            return deny("Approval reviewer is not an active authorized operator.")

        receipt = order_adapter.process_refund(
            db=db,
            organization_id=organization_id,
            order_number=order_number,
            amount=amount,
            reason=reason,
            idempotency_key=proposal.idempotency_key,
            actor_id=actor_id,
        )

        proposal.status = ProposalStatus.EXECUTED
        task.status = TaskStatus.VERIFYING

        db.flush()

        return True, "Refund recorded. Outcome verification is pending.", receipt


action_gateway = DeterministicActionGateway()