from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

def get(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create(db: Session, obj_in: UserCreate) -> User:
    db_obj = User(
        email=obj_in.email,
        password_hash=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
        degree=obj_in.degree,
        year_of_study=obj_in.year_of_study,
        role="student",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, db_obj: User, obj_in: UserUpdate) -> User:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_multi(
    db: Session, page: int = 1, size: int = 20
) -> Tuple[List[User], int]:
    total = db.query(User).count()
    items = db.query(User).offset((page - 1) * size).limit(size).all()
    return items, total