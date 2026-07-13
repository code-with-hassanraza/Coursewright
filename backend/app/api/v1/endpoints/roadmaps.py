from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user, require_role
from app.crud import crud_roadmap
from app.db.session import get_db
from app.models.user import User
from app.schemas.roadmap import RoadmapCreate, RoadmapResponse, RoadmapUpdate

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])
logger = get_logger(__name__)


@router.get(
    "/specialization/{specialization_id}",
    response_model=RoadmapResponse,
)
def get_roadmap_by_specialization(
    specialization_id: UUID,
    db: Session = Depends(get_db),
):
    roadmap = crud_roadmap.get_by_specialization(
        db, specialization_id=specialization_id, status="published"
    )
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published roadmap found for this specialization",
        )
    return roadmap


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
def get_roadmap(
    roadmap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roadmap = crud_roadmap.get(db, roadmap_id=roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )
    return roadmap


@router.post(
    "",
    response_model=RoadmapResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_roadmap(
    obj_in: RoadmapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    roadmap = crud_roadmap.create(db, obj_in=obj_in)
    logger.info(
        f"Roadmap created: {roadmap.title} by {current_user.email}"
    )
    return roadmap


@router.put("/{roadmap_id}", response_model=RoadmapResponse)
def update_roadmap(
    roadmap_id: UUID,
    obj_in: RoadmapUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    roadmap = crud_roadmap.get(db, roadmap_id=roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )
    updated = crud_roadmap.update(db, db_obj=roadmap, obj_in=obj_in)
    logger.info(f"Roadmap updated: {updated.title} by {current_user.email}")
    return updated