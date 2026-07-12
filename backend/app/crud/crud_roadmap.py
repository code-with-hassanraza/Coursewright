from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.roadmap import Roadmap
from app.schemas.roadmap import RoadmapCreate, RoadmapUpdate


def get(db: Session, roadmap_id: UUID) -> Optional[Roadmap]:
    return db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()


def get_by_specialization(
    db: Session, specialization_id: UUID, status: str = "published"
) -> Optional[Roadmap]:
    return (
        db.query(Roadmap)
        .filter(
            Roadmap.specialization_id == specialization_id,
            Roadmap.status == status,
        )
        .first()
    )


def get_multi(
    db: Session, page: int = 1, size: int = 20
) -> Tuple[List[Roadmap], int]:
    total = db.query(Roadmap).count()
    items = db.query(Roadmap).offset((page - 1) * size).limit(size).all()
    return items, total


def create(db: Session, obj_in: RoadmapCreate) -> Roadmap:
    db_obj = Roadmap(
        specialization_id=obj_in.specialization_id,
        title=obj_in.title,
        nodes=[node.model_dump() for node in obj_in.nodes],
        status="draft",
        ai_generated=obj_in.ai_generated,
        version=1,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, db_obj: Roadmap, obj_in: RoadmapUpdate) -> Roadmap:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "nodes" in update_data and update_data["nodes"] is not None:
        update_data["nodes"] = [
            node.model_dump() if hasattr(node, "model_dump") else node
            for node in update_data["nodes"]
        ]
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj