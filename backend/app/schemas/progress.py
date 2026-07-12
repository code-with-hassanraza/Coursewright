from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    specialization_id: UUID
    roadmap_id: Optional[UUID] = None
    status: str
    completed_nodes: List[Any]
    quiz_score: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class ExploreRequest(BaseModel):
    roadmap_id: Optional[UUID] = None
    