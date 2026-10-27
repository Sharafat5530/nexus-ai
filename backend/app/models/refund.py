from sqlalchemy import Column, ForeignKey, Numeric, String

from app.database import Base
from app.models.base import (
    TenantScopedMixin,
    TimestampMixin,
    generate_uuid,
)


class RefundExecution(Base, TimestampMixin, TenantScopedMixin):
    """Receipt for a refund committed to the local order ledger."""

    __tablename__ = "refund_executions"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    idempotency_key = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    order_id = Column(
        String(36),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    amount = Column(Numeric(14, 2), nullable=False)
    previous_refunded_amount = Column(Numeric(14, 2), nullable=False)
    resulting_refunded_amount = Column(Numeric(14, 2), nullable=False)

    currency = Column(String(8), nullable=False)
    reason = Column(String(255), nullable=False)
    actor_id = Column(String(128), nullable=False)