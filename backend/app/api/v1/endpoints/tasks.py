from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.crud import crud_progress, crud_task
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.progress import UserProgressResponse
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = get_logger(__name__)


@router.get(
    "/specialization/{specialization_id}",
    response_model=PaginatedResponse[TaskResponse],
)
def list_tasks(
    specialization_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = crud_task.get_by_specialization(
        db, specialization_id=specialization_id, page=page, size=size
    )
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = crud_task.get(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.post(
    "/{task_id}/complete",
    response_model=UserProgressResponse,
)
def complete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = crud_task.get(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    progress = crud_progress.get_by_user_spec(
        db,
        user_id=current_user.id,
        specialization_id=task.specialization_id,
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must explore this specialization before completing tasks",
        )

    updated = crud_progress.update_node_complete(
        db, db_obj=progress, node_id=str(task_id)
    )
    logger.info(
        f"User {current_user.email} completed task {task_id}"
    )
    return updated