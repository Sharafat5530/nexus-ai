from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, TenantScopedMixin, generate_uuid

class TaskStatus(str, Enum):
    CREATED = "created"
    INVESTIGATING = "investigating"
    ACTION_PROPOSED = "action_proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    FAILED = "failed"

class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    BLOCKED = "blocked"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class Task(Base, TimestampMixin, TenantScopedMixin):
    """The central unit of autonomous teammate work."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.CREATED, nullable=False, index=True)
    priority = Column(String(32), default="medium", nullable=False)
    workflow_type = Column(String(64), default="support_resolution", nullable=False)
    meta = Column(JSON, nullable=True)

    # Relationships
    action_proposals = relationship("ActionProposal", back_populates="task", cascade="all, delete-orphan")
    outcome_evidence = relationship("OutcomeEvidence", back_populates="task", uselist=False, cascade="all, delete-orphan")

class ActionProposal(Base, TimestampMixin, TenantScopedMixin):
    """An action drafted by an agent that must pass the Deterministic Policy Gateway."""
    __tablename__ = "action_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False) # e.g. "stripe_refund", "carrier_upgrade"
    target_entity = Column(String(128), nullable=False) # e.g. "order:ORD-4491"
    payload = Column(JSON, nullable=False) # Parameters (amount, reason, etc.)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    requires_human_approval = Column(Boolean, default=True, nullable=False)
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False, index=True)

    # Relationships
    task = relationship("Task", back_populates="action_proposals")
    approval = relationship("Approval", back_populates="action_proposal", uselist=False, cascade="all, delete-orphan")

class Approval(Base, TimestampMixin, TenantScopedMixin):
    """A human-in-the-loop gate decision for restricted or sensitive operations."""
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_proposal_id = Column(String(36), ForeignKey("action_proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    reviewer_id = Column(String(36), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    action_proposal = relationship("ActionProposal", back_populates="approval")

class OutcomeEvidence(Base, TimestampMixin, TenantScopedMixin):
    """Independent proof-of-outcome read back from the authoritative system."""
    __tablename__ = "outcome_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    expected_outcome = Column(JSON, nullable=False)
    actual_outcome = Column(JSON, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    evidence_summary = Column(Text, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="outcome_evidence")
