from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import User
from app.models.workflow import Approval, ApprovalStatus, ActionProposal, ProposalStatus, Task, TaskStatus
from app.models.audit import AuditEvent, AuditEventType
from app.schemas.workflow import ApprovalRead, ApprovalDecision
from app.core.security import require_operator

router = APIRouter(prefix="/approvals", tags=["Human Approval Queue"])

@router.get("", response_model=List[ApprovalRead])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Retrieves pending approval gates requiring human sign-off."""
    return db.query(Approval).filter(
        Approval.organization_id == current_user.organization_id,
        Approval.status == ApprovalStatus.PENDING
    ).order_by(Approval.created_at.desc()).all()

@router.post("/{approval_id}/approve")
def approve_action(
    approval_id: str,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Signs off on a restricted action proposal. Transition verified by deterministic gateway."""
    approval = db.query(Approval).filter(
        Approval.id == approval_id,
        Approval.organization_id == current_user.organization_id
    ).first()
    if not approval or approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Approval gate not found or already processed")

    # Update approval state
    approval.status = ApprovalStatus.APPROVED
    approval.reviewer_id = current_user.id
    approval.reviewer_notes = decision.notes or "Approved by operator"

    # Update proposal state
    proposal = approval.action_proposal
    proposal.status = ProposalStatus.APPROVED

    # Advance parent task state
    task = proposal.task
    task.status = TaskStatus.APPROVED

    # Log immutable audit event
    audit = AuditEvent(
        organization_id=current_user.organization_id,
        event_type=AuditEventType.ACTION_APPROVED,
        actor_id=current_user.id,
        target_id=proposal.id,
        summary=f"Action '{proposal.action_type}' on '{proposal.target_entity}' APPROVED by {current_user.full_name}",
        details={"reviewer_notes": approval.reviewer_notes, "task_id": task.id},
        idempotency_key=proposal.idempotency_key
    )
    db.add(audit)
    db.commit()

    return {
        "status": "approved",
        "action_proposal_id": proposal.id,
        "task_id": task.id,
        "reviewer": current_user.full_name
    }

@router.post("/{approval_id}/reject")
def reject_action(
    approval_id: str,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Rejects a proposed action. Halts side-effects and informs agent workflow."""
    approval = db.query(Approval).filter(
        Approval.id == approval_id,
        Approval.organization_id == current_user.organization_id
    ).first()
    if not approval or approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Approval gate not found or already processed")

    approval.status = ApprovalStatus.REJECTED
    approval.reviewer_id = current_user.id
    approval.reviewer_notes = decision.notes or "Rejected by operator"

    proposal = approval.action_proposal
    proposal.status = ProposalStatus.REJECTED

    task = proposal.task
    task.status = TaskStatus.FAILED

    audit = AuditEvent(
        organization_id=current_user.organization_id,
        event_type=AuditEventType.ACTION_REJECTED,
        actor_id=current_user.id,
        target_id=proposal.id,
        summary=f"Action '{proposal.action_type}' REJECTED by {current_user.full_name}",
        details={"rejection_notes": approval.reviewer_notes, "task_id": task.id},
        idempotency_key=proposal.idempotency_key
    )
    db.add(audit)
    db.commit()

    return {
        "status": "rejected",
        "action_proposal_id": proposal.id,
        "task_id": task.id,
        "reviewer": current_user.full_name
    }
