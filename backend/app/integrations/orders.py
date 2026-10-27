from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.integrations.base import BaseIntegrationAdapter
from app.models.business_entities import Order, OrderStatus
from app.models.audit import AuditEvent, AuditEventType

class OrderAdapter(BaseIntegrationAdapter):
    """Authoritative adapter for orders, payments, and refunds."""

    @property
    def system_name(self) -> str:
        return "internal_order_system"

    def get_order(self, db: Session, organization_id: str, order_number: str) -> Optional[Order]:
        """Authoritative read of order record."""
        return db.query(Order).filter(
            Order.organization_id == organization_id,
            Order.order_number == order_number
        ).first()

    def process_refund(
        self,
        db: Session,
        organization_id: str,
        order_number: str,
        amount: float,
        reason: str,
        idempotency_key: str,
        actor_id: str = "gateway:action_executor"
    ) -> Dict[str, Any]:
        """
        Executes a partial or full refund on an order with strict idempotency protection.
        """
        # 1. Idempotency Check: Prevent duplicate executions on network retries
        existing_event = db.query(AuditEvent).filter(
            AuditEvent.organization_id == organization_id,
            AuditEvent.idempotency_key == idempotency_key
        ).first()
        if existing_event:
            return {
                "status": "already_executed",
                "message": "Action was already executed with this idempotency key",
                "idempotency_key": idempotency_key
            }

        # 2. Authoritative Record Mutation
        order = self.get_order(db, organization_id, order_number)
        if not order:
            raise ValueError(f"Order {order_number} not found in tenant {organization_id}")

        order.refunded_amount += amount
        if order.refunded_amount >= order.total_amount:
            order.status = OrderStatus.REFUNDED

        # 3. Write Immutable Audit Trail
        audit = AuditEvent(
            organization_id=organization_id,
            event_type=AuditEventType.ACTION_EXECUTED,
            actor_id=actor_id,
            target_id=order.order_number,
            summary=f"Issued ${amount:.2f} refund on order {order_number} ({reason})",
            details={
                "order_number": order_number,
                "amount": amount,
                "new_refunded_total": order.refunded_amount,
                "order_status": order.status.value
            },
            idempotency_key=idempotency_key
        )
        db.add(audit)
        db.commit()
        db.refresh(order)

        return {
            "status": "success",
            "order_number": order.order_number,
            "refunded_amount": amount,
            "total_refunded": order.refunded_amount,
            "order_status": order.status.value,
            "idempotency_key": idempotency_key
        }

order_adapter = OrderAdapter()
