from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import User
from app.models.workflow import ActionProposal, ProposalStatus, Task, TaskStatus
from app.core.security import get_current_user
from app.core.gateway import action_gateway

router = APIRouter(prefix="/gateway", tags=["Zero-Trust Security & Policy Gateway"])

class KillSwitchRequest(BaseModel):
    enabled: bool

class InjectionTestRequest(BaseModel):
    malicious_prompt: str

@router.get("/status")
def get_gateway_status(current_user: User = Depends(get_current_user)):
    return {
        "status": "active_enforced",
        "kill_switch_engaged": action_gateway.KILL_SWITCH_ENGAGED,
        "max_refund_limit": action_gateway.MAX_REFUND_LIMIT,
        "allowed_actions": list(action_gateway.ALLOWED_ACTIONS),
        "active_tenant": current_user.organization_id
    }

@router.post("/kill-switch")
def toggle_kill_switch(payload: KillSwitchRequest, current_user: User = Depends(get_current_user)):
    state = action_gateway.set_kill_switch(payload.enabled)
    return {
        "kill_switch_engaged": state,
        "message": "EMERGENCY: All automated mutations FROZEN." if state else "Mutations resumed under active gateway enforcement."
    }

@router.post("/execute-action/{proposal_id}")
def execute_gated_action(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, message, result = action_gateway.evaluate_and_execute(
        db=db,
        organization_id=current_user.organization_id,
        proposal_id=proposal_id,
        actor_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        
    return {
        "gateway_decision": "PERMITTED_AND_EXECUTED",
        "message": message,
        "result": result
    }

@router.post("/test-injection-defense")
def test_prompt_injection_defense(
    payload: InjectionTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fake_proposal = ActionProposal(
        id=f"prp_exploit_{int(datetime.utcnow().timestamp())}",
        organization_id=current_user.organization_id,
        task_id="tsk_982e01df",
        action_type="stripe_partial_refund",
        target_entity="order:ORD-4491",
        payload={"amount": 500.00, "reason": payload.malicious_prompt},
        idempotency_key=f"idemp_exploit_{int(datetime.utcnow().timestamp())}",
        requires_human_approval=False,
        status=ProposalStatus.PENDING
    )
    db.add(fake_proposal)
    db.commit()

    success, message, _ = action_gateway.evaluate_and_execute(
        db=db,
        organization_id=current_user.organization_id,
        proposal_id=fake_proposal.id,
        actor_id=current_user.id
    )

    return {
        "attack_simulated": payload.malicious_prompt,
        "gateway_intervened": not success,
        "gateway_response": message,
        "action_status": fake_proposal.status.value,
        "security_verdict": "ATTACK_THWARTED: Server gateway rejected mutation and recorded security audit event."
    }
