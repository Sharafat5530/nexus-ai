from enum import Enum
from sqlalchemy import Column, String, JSON
from app.database import Base
from app.models.base import TimestampMixin, TenantScopedMixin, generate_uuid

class AuditEventType(str, Enum):
    ACTION_PROPOSED = "action_proposed"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"
    ACTION_BLOCKED = "action_blocked"
    OUTCOME_VERIFIED = "outcome_verified"
    SECURITY_VIOLATION = "security_violation"
    PROMPT_INJECTION_FLAGGED = "prompt_injection_flagged"

class AuditEvent(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(128), nullable=False)
    target_id = Column(String(128), nullable=True, index=True)
    summary = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
