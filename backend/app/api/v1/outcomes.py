from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import User
from app.models.workflow import Task, OutcomeEvidence
from app.schemas.workflow import OutcomeEvidenceRead
from app.core.security import get_current_user
from app.verification.engine import outcome_engine

router = APIRouter(prefix="/outcomes", tags=["Proof-of-Outcome Verification Engine"])

@router.post("/verify/{task_id}")
def verify_task_outcome(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers independent read-back verification:
    1. Reads actual database records.
    2. Compares against expected state deltas.
    3. Confirms task VERIFIED only if business reality matches.
    """
    success, summary, data = outcome_engine.verify_task_outcome(
        db=db,
        organization_id=current_user.organization_id,
        task_id=task_id,
        actor_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=summary)

    return {
        "status": "VERIFIED",
        "summary": summary,
        "verification_data": data
    }

@router.get("/{task_id}", response_model=OutcomeEvidenceRead)
def get_task_outcome_evidence(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves authoritative cryptographic proof evidence for a task."""
    evidence = db.query(OutcomeEvidence).filter(
        OutcomeEvidence.task_id == task_id,
        OutcomeEvidence.organization_id == current_user.organization_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="No outcome evidence recorded for this task yet.")
    return evidence

@router.post("/recover/{task_id}")
def recover_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Failure Recovery: Safely restarts or recovers a task while honoring idempotency locks."""
    success, summary, data = outcome_engine.recover_failed_task(
        db=db,
        organization_id=current_user.organization_id,
        task_id=task_id,
        actor_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=summary)
    return {
        "status": "recovered",
        "summary": summary,
        "recovery_data": data
    }
