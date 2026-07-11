import uuid

from sqlalchemy import Boolean, Column, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    degree = Column(String(100), nullable=True)
    year_of_study = Column(SmallInteger, nullable=True)
    role = Column(String(20), nullable=False, default="student")
    is_active = Column(Boolean, default=True, nullable=False)

    created_specializations = relationship(
        "Specialization",
        foreign_keys="[Specialization.created_by]",
        back_populates="creator",
    )
    reviewed_specializations = relationship(
        "Specialization",
        foreign_keys="[Specialization.reviewed_by]",
        back_populates="reviewer",
    )
    progress_records = relationship("UserProgress", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")
    review_actions = relationship("Review", back_populates="reviewer")