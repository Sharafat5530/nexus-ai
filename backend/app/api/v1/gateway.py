from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.gateway import action_gateway
from app.core.security import require_admin, require_operator
from app.database import get_db
from app.models.audit import AuditEvent, AuditEventType
from app.models.execution_control import ExecutionControl
from app.models.tenant import User


router = APIRouter(
    prefix="/gateway",
    tags=["Action Gateway"],
)


class KillSwitchRequest(BaseModel):
    enabled: bool


@router.get("/status")
def get_gateway_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    control = db.get(ExecutionControl, "global")

    return {
        "kill_switch_engaged": bool(control and control.paused),
        "max_refund_limit": str(action_gateway.MAX_REFUND_LIMIT),
        "allowed_actions": sorted(action_gateway.ALLOWED_ACTIONS),
        "active_tenant": current_user.organization_id,
        "execution_system": "local_demonstration_ledger",
    }


@router.post("/kill-switch")
def toggle_kill_switch(
    payload: KillSwitchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    control = (
        db.query(ExecutionControl)
        .filter(ExecutionControl.id == "global")
        .with_for_update()
        .first()
    )

    if control is None:
        control = ExecutionControl(id="global")
        db.add(control)

    control.paused = payload.enabled

    db.add(
        AuditEvent(
            organization_id=current_user.organization_id,
            event_type=AuditEventType.SECURITY_VIOLATION,
            actor_id=current_user.id,
            target_id="execution_control:global",
            summary=(
                "Execution paused by administrator"
                if payload.enabled
                else "Execution resumed by administrator"
            ),
            details={
                "control_change": True,
                "paused": payload.enabled,
            },
        )
    )

    try:
        db.commit()
    except (IntegrityError, OperationalError) as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Execution control changed concurrently. Refresh and retry.",
        ) from error

    return {"kill_switch_engaged": control.paused}


@router.post("/execute-action/{proposal_id}")
def execute_gated_action(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    try:
        success, message, receipt = action_gateway.evaluate_and_execute(
            db=db,
            organization_id=current_user.organization_id,
            proposal_id=proposal_id,
            actor_id=current_user.id,
        )

        # Save the execution and state changes together. A denied action
        # may still create an audit entry that needs to be committed.
        db.commit()

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (IntegrityError, OperationalError) as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Execution conflicted with another request. Refresh before retrying.",
        ) from error

    if not success:
        raise HTTPException(status_code=409, detail=message)

    return {
        "gateway_decision": "PERMITTED",
        "message": message,
        "result": receipt,
    }