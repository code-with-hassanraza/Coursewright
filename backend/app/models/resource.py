import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=False)
    node_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    url = Column(Text, nullable=False)
    type = Column(String(30), nullable=True)
    is_free = Column(Boolean, default=True, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    roadmap = relationship("Roadmap", back_populates="resources")