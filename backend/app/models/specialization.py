import uuid

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.db.types import FlexibleJSON


class Specialization(Base, TimestampMixin):
    __tablename__ = "specializations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    real_world_example = Column(Text, nullable=True)
    job_roles = Column(FlexibleJSON, nullable=True, default=list)
    salary_range = Column(String(80), nullable=True)
    prerequisites = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    field = relationship("Field", back_populates="specializations")
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_specializations",
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        back_populates="reviewed_specializations",
    )
    roadmaps = relationship("Roadmap", back_populates="specialization")
    quizzes = relationship("Quiz", back_populates="specialization")
    tasks = relationship("Task", back_populates="specialization")
    progress_records = relationship("UserProgress", back_populates="specialization")
    certificates = relationship("Certificate", back_populates="specialization")
    