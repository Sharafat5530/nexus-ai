from enum import Enum
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum as SQLEnum
from app.database import Base
from app.models.base import TimestampMixin, TenantScopedMixin, generate_uuid

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    REFUNDED = "refunded"

class Customer(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(64), nullable=True)

class Order(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    refunded_amount = Column(Float, default=0.0, nullable=False)

class Shipment(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "shipments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    tracking_number = Column(String(128), unique=True, nullable=False, index=True)
    carrier = Column(String(64), nullable=False)
    status = Column(String(64), default="in_transit", nullable=False)
    destination_city = Column(String(128), nullable=False)
