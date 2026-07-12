from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.crud import crud_progress, crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.progress import UserProgressResponse
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    obj_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    updated = crud_user.update(db, db_obj=user, obj_in=obj_in)
    logger.info(f"User profile updated: {updated.email}")
    return updated


@router.get(
    "/{user_id}/progress",
    response_model=PaginatedResponse[UserProgressResponse],
)
def get_user_progress(
    user_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role not in ("admin", "reviewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    items, total = crud_progress.get_user_progress(
        db, user_id=user_id, page=page, size=size
    )
    return PaginatedResponse(items=items, total=total, page=page, size=size)
    