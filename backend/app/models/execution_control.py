from sqlalchemy import Boolean, Column, String

from app.database import Base


class ExecutionControl(Base):
    __tablename__ = "execution_controls"

    id = Column(String(32), primary_key=True)
    paused = Column(Boolean, nullable=False, default=False)