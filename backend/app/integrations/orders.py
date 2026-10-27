from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.base import BaseIntegrationAdapter
from app.models.audit import AuditEvent, AuditEventType
from app.models.business_entities import Order, OrderStatus
from app.models.refund import RefundExecution


CENT = Decimal("0.01")


def parse_money(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Invalid refund amount.") from error

    if not amount.is_finite() or amount <= 0:
        raise ValueError("Refund amount must be finite and positive.")

    if amount > Decimal("999999999999.99"):
        raise ValueError("Refund amount exceeds the supported range.")

    if amount != amount.quantize(CENT):
        raise ValueError("Refund amount must have at most two decimal places.")

    return amount.quantize(CENT)


class OrderAdapter(BaseIntegrationAdapter):
    """Order access and refunds against the local demonstration ledger."""

    @property
    def system_name(self) -> str:
        return "internal_order_system"

    def get_order(
        self,
        db: Session,
        organization_id: str,
        order_number: str,
    ) -> Order | None:
        return (
            db.query(Order)
            .filter(
                Order.organization_id == organization_id,
                Order.order_number == order_number,
            )
            .first()
        )

    @staticmethod
    def build_receipt(
        execution: RefundExecution,
        order_number: str,
        *,
        repeated: bool,
    ) -> dict[str, Any]:
        return {
            "status": "already_executed" if repeated else "success",
            "execution_id": execution.id,
            "order_number": order_number,
            "refunded_amount": str(execution.amount),
            "previous_refunded_amount": str(
                execution.previous_refunded_amount
            ),
            "total_refunded": str(execution.resulting_refunded_amount),
            "currency": execution.currency,
            "idempotency_key": execution.idempotency_key,
            "system": "local_demonstration_ledger",
        }

    def process_refund(
        self,
        db: Session,
        organization_id: str,
        order_number: str,
        amount: float,
        reason: str,
        idempotency_key: str,
        actor_id: str = "gateway:action_executor",
    ) -> dict[str, Any]:
        credit = parse_money(amount)

        if not idempotency_key or len(idempotency_key) > 128:
            raise ValueError("A valid idempotency key is required.")

        if not reason or len(reason) > 255:
            raise ValueError("Refund reason must contain 1 to 255 characters.")

        order = (
            db.query(Order)
            .filter(
                Order.organization_id == organization_id,
                Order.order_number == order_number,
            )
            .with_for_update()
            .first()
        )

        if order is None:
            raise ValueError("Order not found in the current organization.")

        existing = (
            db.query(RefundExecution)
            .filter(
                RefundExecution.organization_id == organization_id,
                RefundExecution.idempotency_key == idempotency_key,
            )
            .first()
        )

        if existing is not None:
            if (
                existing.order_id != order.id
                or existing.amount != credit
                or existing.reason != reason
                or existing.currency != order.currency
            ):
                raise ValueError(
                    "This idempotency key belongs to a different refund request."
                )

            return self.build_receipt(
                existing,
                order_number,
                repeated=True,
            )

        previous = Decimal(str(order.refunded_amount)).quantize(CENT)
        total = Decimal(str(order.total_amount)).quantize(CENT)
        remaining = total - previous

        if credit > remaining:
            raise ValueError("Refund exceeds the remaining order balance.")

        resulting = previous + credit

        # The existing order schema uses Float. The execution receipt uses
        # fixed precision until the order schema is migrated.
        order.refunded_amount = float(resulting)

        if resulting == total:
            order.status = OrderStatus.REFUNDED

        execution = RefundExecution(
            organization_id=organization_id,
            order_id=order.id,
            idempotency_key=idempotency_key,
            amount=credit,
            previous_refunded_amount=previous,
            resulting_refunded_amount=resulting,
            currency=order.currency,
            reason=reason,
            actor_id=actor_id,
        )

        db.add(execution)
        db.flush()

        receipt = self.build_receipt(
            execution,
            order_number,
            repeated=False,
        )

        db.add(
            AuditEvent(
                organization_id=organization_id,
                event_type=AuditEventType.ACTION_EXECUTED,
                actor_id=actor_id,
                target_id=order_number,
                summary=(
                    f"Local ledger refund of {credit} {order.currency} "
                    f"recorded for order {order_number}"
                ),
                details=receipt,
                idempotency_key=idempotency_key,
            )
        )

        db.flush()
        return receipt


order_adapter = OrderAdapter()