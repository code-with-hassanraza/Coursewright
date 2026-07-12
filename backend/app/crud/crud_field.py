from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.field import Field


def get(db: Session, field_id: UUID) -> Optional[Field]:
    return db.query(Field).filter(Field.id == field_id).first()


def get_multi(
    db: Session, page: int = 1, size: int = 20
) -> Tuple[List[Field], int]:
    total = db.query(Field).count()
    items = db.query(Field).offset((page - 1) * size).limit(size).all()
    return items, total