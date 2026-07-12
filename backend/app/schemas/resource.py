from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResourceBase(BaseModel):
    title: str
    url: str
    type: Optional[str] = None
    is_free: bool = True
    verified: bool = False


class ResourceCreate(ResourceBase):
    roadmap_id: UUID
    node_id: str


class ResourceResponse(ResourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roadmap_id: UUID
    node_id: str
    created_at: datetime