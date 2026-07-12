from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.specialization import Specialization
from app.schemas.specialization import SpecializationCreate, SpecializationUpdate


def get(db: Session, specialization_id: UUID) -> Optional[Specialization]:
    return (
        db.query(Specialization)
        .filter(Specialization.id == specialization_id)
        .first()
    )


def get_multi(
    db: Session,
    page: int = 1,
    size: int = 20,
    field_id: Optional[UUID] = None,
    search: Optional[str] = None,
    status: str = "published",
) -> Tuple[List[Specialization], int]:
    query = db.query(Specialization).filter(Specialization.status == status)
    if field_id:
        query = query.filter(Specialization.field_id == field_id)
    if search:
        query = query.filter(Specialization.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_by_field(
    db: Session, field_id: UUID, page: int = 1, size: int = 20
) -> Tuple[List[Specialization], int]:
    query = db.query(Specialization).filter(
        Specialization.field_id == field_id,
        Specialization.status == "published",
    )
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_all_drafts(
    db: Session, page: int = 1, size: int = 20
) -> Tuple[List[Specialization], int]:
    query = db.query(Specialization).filter(Specialization.status == "draft")
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def create(
    db: Session, obj_in: SpecializationCreate, created_by: UUID
) -> Specialization:
    db_obj = Specialization(
        field_id=obj_in.field_id,
        name=obj_in.name,
        description=obj_in.description,
        real_world_example=obj_in.real_world_example,
        job_roles=obj_in.job_roles or [],
        salary_range=obj_in.salary_range,
        prerequisites=obj_in.prerequisites,
        status="draft",
        created_by=created_by,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(
    db: Session, db_obj: Specialization, obj_in: SpecializationUpdate
) -> Specialization:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj