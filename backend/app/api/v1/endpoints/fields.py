from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_field, crud_specialization
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.field import FieldResponse
from app.schemas.specialization import SpecializationResponse

router = APIRouter(prefix="/fields", tags=["fields"])
logger = get_logger(__name__)


@router.get("", response_model=PaginatedResponse[FieldResponse])
def list_fields(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud_field.get_multi(db, page=page, size=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{field_id}", response_model=FieldResponse)
def get_field(field_id: UUID, db: Session = Depends(get_db)):
    field = crud_field.get(db, field_id=field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
    return field


@router.get(
    "/{field_id}/specializations",
    response_model=PaginatedResponse[SpecializationResponse],
)
def list_field_specializations(
    field_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    field = crud_field.get(db, field_id=field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
    items, total = crud_specialization.get_by_field(
        db, field_id=field_id, page=page, size=size
    )
    return PaginatedResponse(items=items, total=total, page=page, size=size)