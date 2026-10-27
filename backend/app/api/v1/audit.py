from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.tenant import User
from app.models.audit import AuditEvent
from app.core.security import get_current_user

router = APIRouter(prefix="/audit-events", tags=["Zero-Trust Audit Trail"])

class AuditEventRead(BaseModel):
    id: str
    event_type: str
    actor_id: str
    target_id: str | None = None
    summary: str
    details: dict | None = None
    idempotency_key: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[AuditEventRead])
def list_audit_events(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves immutable audit stream scoped strictly to the authenticated tenant."""
    return db.query(AuditEvent).filter(
        AuditEvent.organization_id == current_user.organization_id
    ).order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
