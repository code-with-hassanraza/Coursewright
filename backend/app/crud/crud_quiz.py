from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.quiz import Quiz
from app.schemas.quiz import QuizCreate


def get(db: Session, quiz_id: UUID) -> Optional[Quiz]:
    return db.query(Quiz).filter(Quiz.id == quiz_id).first()


def get_by_specialization(
    db: Session, specialization_id: UUID
) -> Optional[Quiz]:
    return (
        db.query(Quiz)
        .filter(Quiz.specialization_id == specialization_id)
        .first()
    )


def create(db: Session, obj_in: QuizCreate) -> Quiz:
    db_obj = Quiz(
        specialization_id=obj_in.specialization_id,
        title=obj_in.title,
        questions=[q.model_dump() for q in obj_in.questions],
        pass_score=obj_in.pass_score,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj