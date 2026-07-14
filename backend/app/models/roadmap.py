import uuid

from sqlalchemy import Boolean, Column, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.db.types import FlexibleJSON


class Roadmap(Base, TimestampMixin):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialization_id = Column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    title = Column(String(200), nullable=False)
    nodes = Column(FlexibleJSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="draft")
    ai_generated = Column(Boolean, default=False, nullable=False)
    version = Column(SmallInteger, default=1, nullable=False)

    specialization = relationship("Specialization", back_populates="roadmaps")
    resources = relationship("Resource", back_populates="roadmap")
    progress_records = relationship("UserProgress", back_populates="roadmap")
