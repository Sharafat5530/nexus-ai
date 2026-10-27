from enum import Enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, TenantScopedMixin, generate_uuid

class MessageSender(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    OPERATOR = "operator"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class Conversation(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False)
    channel = Column(String(32), default="web_chat", nullable=False)

    # Relationships
    customer = relationship("Customer")
    task = relationship("Task")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(SQLEnum(MessageSender), nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
