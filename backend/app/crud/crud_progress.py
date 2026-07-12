from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user_progress import UserProgress


def get_by_user_spec(
    db: Session, user_id: UUID, specialization_id: UUID
) -> Optional[UserProgress]:
    return (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.specialization_id == specialization_id,
        )
        .first()
    )


def get_user_progress(
    db: Session, user_id: UUID, page: int = 1, size: int = 20
) -> Tuple[List[UserProgress], int]:
    query = db.query(UserProgress).filter(UserProgress.user_id == user_id)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def create_explore(
    db: Session,
    user_id: UUID,
    specialization_id: UUID,
    roadmap_id: Optional[UUID] = None,
) -> UserProgress:
    db_obj = UserProgress(
        user_id=user_id,
        specialization_id=specialization_id,
        roadmap_id=roadmap_id,
        status="exploring",
        completed_nodes=[],
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_node_complete(
    db: Session, db_obj: UserProgress, node_id: str
) -> UserProgress:
    completed = list(db_obj.completed_nodes or [])
    if node_id not in completed:
        completed.append(node_id)
    db_obj.completed_nodes = completed
    db_obj.status = "learning"
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_quiz_score(
    db: Session, db_obj: UserProgress, score: int
) -> UserProgress:
    db_obj.quiz_score = score
    db.commit()
    db.refresh(db_obj)
    return db_obj


def mark_completed(db: Session, db_obj: UserProgress) -> UserProgress:
    from datetime import datetime, timezone
    db_obj.status = "completed"
    db_obj.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    return db_obj