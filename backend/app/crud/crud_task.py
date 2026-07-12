from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate


def get(db: Session, task_id: UUID) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def get_by_specialization(
    db: Session, specialization_id: UUID, page: int = 1, size: int = 20
) -> Tuple[List[Task], int]:
    query = db.query(Task).filter(Task.specialization_id == specialization_id)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def create(db: Session, obj_in: TaskCreate) -> Task:
    db_obj = Task(
        specialization_id=obj_in.specialization_id,
        title=obj_in.title,
        description=obj_in.description,
        instructions=obj_in.instructions,
        difficulty=obj_in.difficulty,
        suggested_tools=obj_in.suggested_tools or [],
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj