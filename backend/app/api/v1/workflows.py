from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import User
from app.models.workflow import Task, TaskStatus, ActionProposal, ProposalStatus, Approval, ApprovalStatus
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.audit import AuditEvent, AuditEventType
from app.agents.graph import workflow_graph
from app.core.security import get_current_user

router = APIRouter(prefix="/workflows", tags=["LangGraph Multi-Agent Orchestrator"])

class WorkflowExecutionRequest(BaseModel):
    message: str
    customer_id: Optional[str] = "cust_marcus_vance_01"
    conversation_id: Optional[str] = "cnv_marcus_vance_01"

class AgentTraceItem(BaseModel):
    agent: str
    action: str
    thought: str
    output: Dict[str, Any]
    timestamp: str

class WorkflowExecutionResponse(BaseModel):
    task_id: str
    status: str
    final_response: str
    proposed_action: Optional[Dict[str, Any]] = None
    requires_approval: bool
    agent_traces: List[AgentTraceItem]

@router.post("/execute", response_model=WorkflowExecutionResponse)
def execute_agent_workflow(
    payload: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes the multi-agent LangGraph workflow:
    1. Orchestrator classifies query and identifies order.
    2. Operations reads authoritative database status.
    3. Policy Research retrieves reimbursement rules.
    4. Proposal Synthesizer creates an Action Proposal.
    5. Persists the task and approval gate into the database.
    """
    task_id = f"tsk_auto_{int(datetime.utcnow().timestamp())}"
    
    # Initial LangGraph State
    initial_state = {
        "organization_id": current_user.organization_id,
        "customer_id": payload.customer_id,
        "conversation_id": payload.conversation_id,
        "task_id": task_id,
        "user_message": payload.message,
        "extracted_order_number": None,
        "order_data": None,
        "shipment_data": None,
        "policy_data": None,
        "proposed_action": None,
        "requires_approval": True,
        "agent_logs": [],
        "current_agent": "Starting",
        "final_response": ""
    }
    
    # Run LangGraph Graph
    final_state = workflow_graph.invoke(initial_state)
    
    # Persist the newly generated Task in Database
    new_task = Task(
        id=task_id,
        organization_id=current_user.organization_id,
        customer_id=payload.customer_id,
        title=f"Resolve Order Issue #{final_state.get('extracted_order_number', 'ORD-4491')}",
        description=payload.message,
        status=TaskStatus.AWAITING_APPROVAL if final_state.get("requires_approval") else TaskStatus.INVESTIGATING,
        priority="high",
        workflow_type="delayed_order_resolution",
        meta={"traces": final_state.get("agent_logs", [])}
    )
    db.add(new_task)
    
    # Persist the Action Proposal & Approval Gate if generated
    proposal_data = final_state.get("proposed_action")
    if proposal_data:
        proposal_id = f"prp_{int(datetime.utcnow().timestamp())}"
        proposal = ActionProposal(
            id=proposal_id,
            organization_id=current_user.organization_id,
            task_id=new_task.id,
            action_type=proposal_data["action_type"],
            target_entity=proposal_data["target_entity"],
            payload=proposal_data["payload"],
            idempotency_key=proposal_data["idempotency_key"],
            requires_human_approval=proposal_data["requires_human_approval"],
            status=ProposalStatus.PENDING
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        
        # If restricted, create human approval record
        if proposal.requires_human_approval:
            approval = Approval(
                id=f"appr_{int(datetime.utcnow().timestamp())}",
                organization_id=current_user.organization_id,
                action_proposal_id=proposal.id,
                status=ApprovalStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(approval)
            
        # Log to Audit Stream
        audit = AuditEvent(
            organization_id=current_user.organization_id,
            event_type=AuditEventType.ACTION_PROPOSED,
            actor_id="agent:proposal_synthesizer",
            target_id=proposal.id,
            summary=f"Multi-Agent Workflow proposed {proposal.action_type} for {proposal.target_entity}",
            details={"traces_count": len(final_state.get("agent_logs", []))},
            idempotency_key=proposal.idempotency_key
        )
        db.add(audit)
        
    db.commit()
    
    # Append response to conversation if active
    if payload.conversation_id:
        reply_msg = Message(
            organization_id=current_user.organization_id,
            conversation_id=payload.conversation_id,
            sender=MessageSender.AGENT,
            content=final_state.get("final_response", "")
        )
        db.add(reply_msg)
        db.commit()
        
    return WorkflowExecutionResponse(
        task_id=new_task.id,
        status=new_task.status.value,
        final_response=final_state.get("final_response", ""),
        proposed_action=proposal_data,
        requires_approval=final_state.get("requires_approval", True),
        agent_traces=final_state.get("agent_logs", [])
    )

@router.get("/{task_id}/trace")
def get_task_agent_trace(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the granular reasoning and tool-execution logs for a task."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.organization_id == current_user.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    traces = task.meta.get("traces", []) if task.meta else []
    return {
        "task_id": task.id,
        "status": task.status.value,
        "traces": traces
    }
