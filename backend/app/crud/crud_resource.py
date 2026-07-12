from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.schemas.resource import ResourceCreate


def get(db: Session, resource_id: UUID) -> Optional[Resource]:
    return db.query(Resource).filter(Resource.id == resource_id).first()


def get_by_node(db: Session, node_id: str) -> List[Resource]:
    return db.query(Resource).filter(Resource.node_id == node_id).all()


def create(db: Session, obj_in: ResourceCreate) -> Resource:
    db_obj = Resource(
        roadmap_id=obj_in.roadmap_id,
        node_id=obj_in.node_id,
        title=obj_in.title,
        url=obj_in.url,
        type=obj_in.type,
        is_free=obj_in.is_free,
        verified=obj_in.verified,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete(db: Session, resource_id: UUID) -> bool:
    db_obj = get(db, resource_id)
    if not db_obj:
        return False
    db.delete(db_obj)
    db.commit()
    return True