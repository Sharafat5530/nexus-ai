from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_operator
from app.database import get_db
from app.models.business_entities import Customer
from app.models.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageSender,
)
from app.models.tenant import User
from app.schemas.conversation import (
    ConversationRead,
    ConversationStart,
    MessageCreate,
    MessageRead,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Operator Conversations"],
)


def find_conversation(
    db: Session,
    organization_id: str,
    conversation_id: str,
) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == organization_id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    return (
        db.query(Conversation)
        .filter(
            Conversation.organization_id == current_user.organization_id,
        )
        .order_by(
            Conversation.created_at.desc(),
            Conversation.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def start_or_get_conversation(
    payload: ConversationStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    email = str(payload.customer_email).lower()

    customers = (
        db.query(Customer)
        .filter(
            Customer.organization_id == current_user.organization_id,
            func.lower(Customer.email) == email,
        )
        .limit(2)
        .all()
    )

    if not customers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    if len(customers) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple customer records match this email. Resolve the duplicates first.",
        )

    customer = customers[0]

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.organization_id == current_user.organization_id,
            Conversation.customer_id == customer.id,
            Conversation.status.in_(
                [
                    ConversationStatus.OPEN,
                    ConversationStatus.INVESTIGATING,
                ]
            ),
        )
        .order_by(Conversation.created_at.desc())
        .first()
    )

    if conversation is None:
        conversation = Conversation(
            organization_id=current_user.organization_id,
            customer_id=customer.id,
            status=ConversationStatus.OPEN,
            channel="operator_console",
        )

        db.add(conversation)
        db.flush()

    if payload.initial_message:
        db.add(
            Message(
                organization_id=current_user.organization_id,
                conversation_id=conversation.id,
                sender=MessageSender.OPERATOR,
                content=payload.initial_message,
                meta={"operator_id": current_user.id},
            )
        )

    db.commit()
    db.refresh(conversation)

    return conversation


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def post_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    conversation = find_conversation(
        db,
        current_user.organization_id,
        conversation_id,
    )

    if conversation.status == ConversationStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This conversation is resolved. Start a new conversation.",
        )

    message = Message(
        organization_id=current_user.organization_id,
        conversation_id=conversation.id,
        sender=MessageSender.OPERATOR,
        content=payload.content,
        meta={"operator_id": current_user.id},
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageRead],
)
def get_conversation_history(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    conversation = find_conversation(
        db,
        current_user.organization_id,
        conversation_id,
    )

    return (
        db.query(Message)
        .filter(
            Message.organization_id == current_user.organization_id,
            Message.conversation_id == conversation.id,
        )
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )