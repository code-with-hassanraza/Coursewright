from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.crud import crud_progress, crud_quiz
from app.db.session import get_db
from app.models.user import User
from app.schemas.quiz import QuizResponse, QuizResult, QuizSubmit

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
logger = get_logger(__name__)


@router.get(
    "/specialization/{specialization_id}",
    response_model=QuizResponse,
)
def get_quiz(
    specialization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = crud_quiz.get_by_specialization(
        db, specialization_id=specialization_id
    )
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz found for this specialization",
        )
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: UUID,
    obj_in: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = crud_quiz.get(db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    # Grade the quiz
    questions = quiz.questions
    total = len(questions)
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions",
        )

    correct_count = 0
    for q in questions:
        question_id = q.get("id")
        correct_answer = q.get("correct")
        submitted_answer = obj_in.answers.get(question_id)
        if submitted_answer and submitted_answer == correct_answer:
            correct_count += 1

    score = int((correct_count / total) * 100)
    passed = score >= quiz.pass_score

    # Update progress record if it exists
    progress = crud_progress.get_by_user_spec(
        db,
        user_id=current_user.id,
        specialization_id=quiz.specialization_id,
    )
    if progress:
        crud_progress.update_quiz_score(db, db_obj=progress, score=score)

    logger.info(
        f"User {current_user.email} scored {score}% on quiz {quiz_id} "
        f"({'passed' if passed else 'failed'})"
    )

    return QuizResult(
        score=score,
        passed=passed,
        pass_score=quiz.pass_score,
        correct=correct_count,
        total=total,
    )