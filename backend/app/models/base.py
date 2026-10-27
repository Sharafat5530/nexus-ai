import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TenantScopedMixin:
    organization_id = Column(String(36), nullable=False, index=True)

def generate_uuid() -> str:
    return str(uuid.uuid4())
