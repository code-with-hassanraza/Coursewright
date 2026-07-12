import secrets
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.certificate import Certificate


def get_by_user(db: Session, user_id: UUID) -> List[Certificate]:
    return db.query(Certificate).filter(Certificate.user_id == user_id).all()


def get_by_code(db: Session, code: str) -> Optional[Certificate]:
    return (
        db.query(Certificate)
        .filter(Certificate.certificate_code == code)
        .first()
    )


def exists(db: Session, user_id: UUID, specialization_id: UUID) -> bool:
    return (
        db.query(Certificate)
        .filter(
            Certificate.user_id == user_id,
            Certificate.specialization_id == specialization_id,
        )
        .first()
        is not None
    )


def create(
    db: Session, user_id: UUID, specialization_id: UUID
) -> Certificate:
    code = secrets.token_urlsafe(32)[:64]
    db_obj = Certificate(
        user_id=user_id,
        specialization_id=specialization_id,
        certificate_code=code,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj