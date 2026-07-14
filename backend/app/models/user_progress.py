import uuid

from sqlalchemy import (
    Column, DateTime, ForeignKey, SmallInteger,
    String, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.types import FlexibleJSON


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    specialization_id = Column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=True)
    status = Column(String(20), nullable=False, default="exploring")
    completed_nodes = Column(FlexibleJSON, nullable=False, default=list)
    quiz_score = Column(SmallInteger, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "specialization_id", name="uq_user_specialization"),
    )

    user = relationship("User", back_populates="progress_records")
    specialization = relationship("Specialization", back_populates="progress_records")
    roadmap = relationship("Roadmap", back_populates="progress_records")
    