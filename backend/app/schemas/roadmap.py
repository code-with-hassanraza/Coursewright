from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoadmapNode(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str = "topic"
    order: int
    parent_id: Optional[str] = None
    estimated_hours: Optional[int] = None
    resources: List[Any] = []


class RoadmapCreate(BaseModel):
    specialization_id: UUID
    title: str
    nodes: List[RoadmapNode] = []
    ai_generated: bool = False


class RoadmapUpdate(BaseModel):
    title: Optional[str] = None
    nodes: Optional[List[RoadmapNode]] = None
    status: Optional[str] = None
    ai_generated: Optional[bool] = None
    version: Optional[int] = None


class RoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    specialization_id: UUID
    title: str
    nodes: List[Dict[str, Any]]
    status: str
    ai_generated: bool
    version: int
    created_at: datetime
    updated_at: datetime