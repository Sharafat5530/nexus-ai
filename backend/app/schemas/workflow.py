from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: Optional[str] = "medium"
    workflow_type: Optional[str] = "support_resolution"
    customer_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class ActionProposalRead(BaseModel):
    id: str
    action_type: str
    target_entity: str
    payload: Dict[str, Any]
    idempotency_key: str
    requires_human_approval: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class OutcomeEvidenceRead(BaseModel):
    id: str
    is_verified: bool
    evidence_summary: str
    expected_outcome: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskRead(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    workflow_type: str
    customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    action_proposals: List[ActionProposalRead] = []
    outcome_evidence: Optional[OutcomeEvidenceRead] = None

    class Config:
        from_attributes = True

class ApprovalRead(BaseModel):
    id: str
    status: str
    reviewer_notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    action_proposal: ActionProposalRead

    class Config:
        from_attributes = True

class ApprovalDecision(BaseModel):
    notes: Optional[str] = None
