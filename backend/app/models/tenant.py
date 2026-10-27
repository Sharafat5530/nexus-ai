from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT_OPERATOR = "agent_operator"
    AUDITOR = "auditor"
    CUSTOMER = "customer"

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.AGENT_OPERATOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    organization = relationship("Organization", back_populates="users")
