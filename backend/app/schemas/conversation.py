from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str
    sender: Optional[str] = "customer"

class MessageRead(BaseModel):
    id: str
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationStart(BaseModel):
    customer_email: str
    initial_message: Optional[str] = None

class ConversationRead(BaseModel):
    id: str
    customer_id: str
    task_id: Optional[str] = None
    status: str
    channel: str
    created_at: datetime
    messages: List[MessageRead] = []

    class Config:
        from_attributes = True
