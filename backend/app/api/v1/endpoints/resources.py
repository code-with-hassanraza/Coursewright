from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import require_role
from app.crud import crud_resource
from app.db.session import get_db
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])
logger = get_logger(__name__)


@router.get("/node/{node_id}", response_model=list[ResourceResponse])
def get_resources_by_node(
    node_id: str,
    db: Session = Depends(get_db),
):
    resources = crud_resource.get_by_node(db, node_id=node_id)
    return resources


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    obj_in: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    resource = crud_resource.create(db, obj_in=obj_in)
    logger.info(
        f"Resource created: {resource.title} by {current_user.email}"
    )
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    deleted = crud_resource.delete(db, resource_id=resource_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    logger.info(
        f"Resource {resource_id} deleted by {current_user.email}"
    )