from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.specialization import Specialization
from app.models.roadmap import Roadmap


def get(db: Session, review_id: UUID) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def get_pending(
    db: Session, page: int = 1, size: int = 20
) -> Tuple[List[Review], int]:
    query = db.query(Review).filter(Review.status == "pending")
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def create(
    db: Session,
    content_type: str,
    content_id: UUID,
    reviewer_id: UUID,
) -> Review:
    db_obj = Review(
        content_type=content_type,
        content_id=content_id,
        reviewer_id=reviewer_id,
        status="pending",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def approve(
    db: Session, db_obj: Review, notes: Optional[str] = None
) -> Review:
    from datetime import datetime, timezone
    db_obj.status = "approved"
    db_obj.notes = notes
    db_obj.reviewed_at = datetime.now(timezone.utc)

    # Publish the content
    if db_obj.content_type == "specialization":
        content = (
            db.query(Specialization)
            .filter(Specialization.id == db_obj.content_id)
            .first()
        )
    else:
        content = (
            db.query(Roadmap)
            .filter(Roadmap.id == db_obj.content_id)
            .first()
        )
    if content:
        content.status = "published"

    db.commit()
    db.refresh(db_obj)
    return db_obj


def reject(
    db: Session, db_obj: Review, notes: Optional[str] = None
) -> Review:
    from datetime import datetime, timezone
    db_obj.status = "rejected"
    db_obj.notes = notes
    db_obj.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    return db_obj