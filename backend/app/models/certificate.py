import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    specialization_id = Column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    certificate_code = Column(String(64), unique=True, nullable=False)
    issued_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="certificates")
    specialization = relationship("Specialization", back_populates="certificates")