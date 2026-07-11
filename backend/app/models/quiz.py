import uuid

from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialization_id = Column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    title = Column(String(200), nullable=False)
    questions = Column(JSONB, nullable=False, default=list)
    pass_score = Column(SmallInteger, default=70, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    specialization = relationship("Specialization", back_populates="quizzes")