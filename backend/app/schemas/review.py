from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content_type: str
    content_id: UUID
    reviewer_id: UUID
    status: str
    notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ReviewAction(BaseModel):
    notes: Optional[str] = None

    