from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MessageCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    content: str = Field(min_length=1, max_length=4000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str
    content: str
    created_at: datetime


class ConversationStart(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    customer_email: EmailStr
    initial_message: str | None = Field(
        default=None,
        min_length=1,
        max_length=4000,
    )


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    task_id: str | None = None
    status: str
    channel: str
    created_at: datetime
    messages: list[MessageRead] = Field(default_factory=list)