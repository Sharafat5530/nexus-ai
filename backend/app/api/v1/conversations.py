from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.business_entities import Customer
from app.models.conversation import Conversation, Message, MessageSender, ConversationStatus
from app.models.workflow import Task, TaskStatus
from app.schemas.conversation import ConversationStart, ConversationRead, MessageCreate, MessageRead

router = APIRouter(prefix="/conversations", tags=["Customer Portal & Chat Ingestion"])

@router.get("", response_model=List[ConversationRead])
def list_conversations(db: Session = Depends(get_db)):
    """Lists all customer conversations with their full message history."""
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()

@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def start_or_get_conversation(payload: ConversationStart, db: Session = Depends(get_db)):
    """Customer portal starts or resumes a support conversation."""
    customer = db.query(Customer).filter(Customer.email == payload.customer_email).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in tenant system")

    convo = db.query(Conversation).filter(
        Conversation.customer_id == customer.id,
        Conversation.status != ConversationStatus.RESOLVED
    ).first()

    if not convo:
        convo = Conversation(
            organization_id=customer.organization_id,
            customer_id=customer.id,
            status=ConversationStatus.OPEN,
            channel="customer_portal"
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)

    if payload.initial_message:
        msg = Message(
            organization_id=customer.organization_id,
            conversation_id=convo.id,
            sender=MessageSender.CUSTOMER,
            content=payload.initial_message
        )
        db.add(msg)
        db.commit()
        db.refresh(convo)

    return convo

@router.post("/{conversation_id}/messages", response_model=MessageRead)
def post_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db)
):
    """Customer sends message. Connects automatically to task orchestration."""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    sender_enum = MessageSender.CUSTOMER if payload.sender == "customer" else MessageSender.AGENT

    msg = Message(
        organization_id=convo.organization_id,
        conversation_id=convo.id,
        sender=sender_enum,
        content=payload.content
    )
    db.add(msg)

    if convo.task_id:
        task = db.query(Task).filter(Task.id == convo.task_id).first()
        if task and task.status == TaskStatus.CREATED:
            task.status = TaskStatus.INVESTIGATING

    db.commit()
    db.refresh(msg)
    return msg

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    """Returns chronologically ordered message history."""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo.messages
