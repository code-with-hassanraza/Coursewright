from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: str
    difficulty: str = "beginner"
    suggested_tools: Optional[List[str]] = None


class TaskCreate(TaskBase):
    specialization_id: UUID


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    specialization_id: UUID
    created_at: datetime