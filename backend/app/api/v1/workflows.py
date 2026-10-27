from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.agents.graph import workflow_graph
from app.core.security import require_operator
from app.database import get_db
from app.models.audit import AuditEvent, AuditEventType
from app.models.business_entities import Customer
from app.models.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageSender,
)
from app.models.tenant import User
from app.models.workflow import (
    ActionProposal,
    Approval,
    ApprovalStatus,
    ProposalStatus,
    Task,
    TaskStatus,
)


router = APIRouter(
    prefix="/workflows",
    tags=["Support Workflows"],
)


class WorkflowExecutionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    message: str = Field(min_length=1, max_length=4000)
    customer_id: str = Field(min_length=1, max_length=36)
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )


class AgentTraceItem(BaseModel):
    agent: str
    action: str
    thought: str
    output: dict[str, Any]
    timestamp: str


class WorkflowExecutionResponse(BaseModel):
    task_id: str
    conversation_id: str
    status: str
    final_response: str
    proposed_action: dict[str, Any] | None = None
    requires_approval: bool
    agent_traces: list[AgentTraceItem]


@router.post("/execute", response_model=WorkflowExecutionResponse)
def execute_agent_workflow(
    payload: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    organization_id = current_user.organization_id

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == payload.customer_id,
            Customer.organization_id == organization_id,
        )
        .first()
    )

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")

    conversation = None

    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == payload.conversation_id,
                Conversation.organization_id == organization_id,
                Conversation.customer_id == customer.id,
            )
            .with_for_update()
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found for this customer.",
            )

        if conversation.status == ConversationStatus.RESOLVED:
            raise HTTPException(
                status_code=409,
                detail="This conversation is resolved.",
            )

        if conversation.task_id:
            previous_task = (
                db.query(Task)
                .filter(
                    Task.id == conversation.task_id,
                    Task.organization_id == organization_id,
                )
                .first()
            )

            if previous_task is None or previous_task.status not in {
                TaskStatus.VERIFIED,
                TaskStatus.FAILED,
            }:
                raise HTTPException(
                    status_code=409,
                    detail="This conversation already has an active task.",
                )

    task_id = str(uuid4())

    initial_state = {
        "organization_id": organization_id,
        "customer_id": customer.id,
        "conversation_id": conversation.id if conversation else None,
        "task_id": task_id,
        "user_message": payload.message,
        "extracted_order_number": None,
        "order_data": None,
        "shipment_data": None,
        "policy_data": None,
        "proposed_action": None,
        "requires_approval": False,
        "agent_logs": [],
        "current_agent": "Starting",
        "final_response": "",
    }

    final_state = workflow_graph.invoke(initial_state)
    proposal_data = final_state.get("proposed_action")
    response = final_state.get("final_response", "")
    traces = final_state.get("agent_logs", [])

    task = Task(
        id=task_id,
        organization_id=organization_id,
        customer_id=customer.id,
        title=(
            f"Review order {final_state['extracted_order_number']}"
            if final_state.get("extracted_order_number")
            else "Clarify customer order request"
        ),
        description=payload.message,
        status=(
            TaskStatus.AWAITING_APPROVAL
            if proposal_data
            else TaskStatus.INVESTIGATING
        ),
        priority="medium",
        workflow_type="delayed_order_resolution",
        meta={"traces": traces},
    )

    db.add(task)
    db.flush()

    if conversation is None:
        conversation = Conversation(
            organization_id=organization_id,
            customer_id=customer.id,
            channel="operator_console",
            status=ConversationStatus.INVESTIGATING,
        )
        db.add(conversation)

    conversation.task_id = task.id
    conversation.status = ConversationStatus.INVESTIGATING
    db.flush()

    if proposal_data:
        proposal = ActionProposal(
            id=str(uuid4()),
            organization_id=organization_id,
            task_id=task.id,
            action_type=proposal_data["action_type"],
            target_entity=proposal_data["target_entity"],
            payload=proposal_data["payload"],
            idempotency_key=proposal_data["idempotency_key"],
            requires_human_approval=True,
            status=ProposalStatus.PENDING,
        )

        db.add(proposal)
        db.flush()

        db.add(
            Approval(
                id=str(uuid4()),
                organization_id=organization_id,
                action_proposal_id=proposal.id,
                status=ApprovalStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
        )

        db.add(
            AuditEvent(
                organization_id=organization_id,
                event_type=AuditEventType.ACTION_PROPOSED,
                actor_id=current_user.id,
                target_id=proposal.id,
                summary="Support workflow created a refund proposal.",
                details={
                    "task_id": task.id,
                    "policy_source": "local_demonstration_rule",
                },
                idempotency_key=proposal.idempotency_key,
            )
        )

    db.add_all(
        [
            Message(
                organization_id=organization_id,
                conversation_id=conversation.id,
                sender=MessageSender.OPERATOR,
                content=payload.message,
                meta={"operator_id": current_user.id},
            ),
            Message(
                organization_id=organization_id,
                conversation_id=conversation.id,
                sender=MessageSender.AGENT,
                content=response,
            ),
        ]
    )

    db.commit()

    return WorkflowExecutionResponse(
        task_id=task.id,
        conversation_id=conversation.id,
        status=task.status.value,
        final_response=response,
        proposed_action=proposal_data,
        requires_approval=proposal_data is not None,
        agent_traces=traces,
    )


@router.get("/{task_id}/trace")
def get_task_agent_trace(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.organization_id == current_user.organization_id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {
        "task_id": task.id,
        "status": task.status.value,
        "traces": (task.meta or {}).get("traces", []),
    }