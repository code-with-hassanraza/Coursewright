from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user, require_role
from app.crud import crud_progress, crud_specialization
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.progress import ExploreRequest, UserProgressResponse
from app.schemas.specialization import (
    SpecializationCreate,
    SpecializationResponse,
    SpecializationUpdate,
)

router = APIRouter(prefix="/specializations", tags=["specializations"])
logger = get_logger(__name__)


@router.get("", response_model=PaginatedResponse[SpecializationResponse])
def list_specializations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    field_id: UUID = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    items, total = crud_specialization.get_multi(
        db, page=page, size=size, field_id=field_id, search=search
    )
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{specialization_id}", response_model=SpecializationResponse)
def get_specialization(
    specialization_id: UUID,
    db: Session = Depends(get_db),
):
    spec = crud_specialization.get(db, specialization_id=specialization_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialization not found",
        )
    return spec


@router.post(
    "",
    response_model=SpecializationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_specialization(
    obj_in: SpecializationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    spec = crud_specialization.create(
        db, obj_in=obj_in, created_by=current_user.id
    )
    logger.info(f"Specialization created: {spec.name} by {current_user.email}")
    return spec


@router.put("/{specialization_id}", response_model=SpecializationResponse)
def update_specialization(
    specialization_id: UUID,
    obj_in: SpecializationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    spec = crud_specialization.get(db, specialization_id=specialization_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialization not found",
        )
    updated = crud_specialization.update(db, db_obj=spec, obj_in=obj_in)
    logger.info(f"Specialization updated: {updated.name}")
    return updated


@router.post(
    "/{specialization_id}/explore",
    response_model=UserProgressResponse,
    status_code=status.HTTP_201_CREATED,
)
def explore_specialization(
    specialization_id: UUID,
    obj_in: ExploreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = crud_specialization.get(db, specialization_id=specialization_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialization not found",
        )
    existing = crud_progress.get_by_user_spec(
        db, user_id=current_user.id, specialization_id=specialization_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already exploring this specialization",
        )
    progress = crud_progress.create_explore(
        db,
        user_id=current_user.id,
        specialization_id=specialization_id,
        roadmap_id=obj_in.roadmap_id,
    )
    logger.info(
        f"User {current_user.email} started exploring: {spec.name}"
    )
    return progress