import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.types import FlexibleJSON


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialization_id = Column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False, default="beginner")
    suggested_tools = Column(FlexibleJSON, nullable=True, default=list)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    specialization = relationship("Specialization", back_populates="tasks")
    