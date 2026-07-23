from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.schemas.roadmap import RoadmapResponse
from app.schemas.review import ReviewResponse
from app.core.logging import get_logger
from app.core.security import require_role
from app.crud import crud_review, crud_specialization, crud_roadmap
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewAction, ReviewResponse
from app.schemas.specialization import SpecializationResponse
from app.schemas.roadmap import RoadmapResponse

router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


@router.get(
    "/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
def list_pending_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer")),
):
    items, total = crud_review.get_pending(db, page=page, size=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.post(
    "/reviews/{review_id}/approve",
    response_model=ReviewResponse,
)
def approve_review(
    review_id: UUID,
    obj_in: ReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer")),
):
    review = crud_review.get(db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review is already {review.status}",
        )
    updated = crud_review.approve(db, db_obj=review, notes=obj_in.notes)
    logger.info(
        f"Review {review_id} approved by {current_user.email} "
        f"→ {review.content_type} {review.content_id} published"
    )
    return updated


@router.post(
    "/reviews/{review_id}/reject",
    response_model=ReviewResponse,
)
def reject_review(
    review_id: UUID,
    obj_in: ReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer")),
):
    review = crud_review.get(db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review is already {review.status}",
        )
    updated = crud_review.reject(db, db_obj=review, notes=obj_in.notes)
    logger.info(
        f"Review {review_id} rejected by {current_user.email}"
    )
    return updated


@router.get(
    "/content/drafts",
    response_model=PaginatedResponse[SpecializationResponse],
)
def list_drafts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer")),
):
    items, total = crud_specialization.get_all_drafts(
        db, page=page, size=size
    )
    return PaginatedResponse(items=items, total=total, page=page, size=size)

class GenerateRoadmapResponse(BaseModel):
    roadmap_id: str
    review_id: str
    message: str

@router.post(
    "/generate-roadmap/{specialization_id}",
    response_model=GenerateRoadmapResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_roadmap(
    specialization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Trigger full AI pipeline:
    specialization → AI nodes → AI resources → draft roadmap → pending review
    """
    from app.services.review_service import trigger_generation

    logger.info(
        f"AI roadmap generation triggered for specialization "
        f"{specialization_id} by {current_user.email}"
    )

    result = trigger_generation(
        specialization_id=specialization_id,
        reviewer_id=current_user.id,
        db=db,
    )

    return GenerateRoadmapResponse(
        roadmap_id=str(result["roadmap"].id),
        review_id=str(result["review"].id),
        message=f"Roadmap generated with {len(result['roadmap'].nodes)} nodes. Pending review.",
    )