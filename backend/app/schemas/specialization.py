from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SpecializationBase(BaseModel):
    name: str
    description: Optional[str] = None
    real_world_example: Optional[str] = None
    job_roles: Optional[List[str]] = None
    salary_range: Optional[str] = None
    prerequisites: Optional[str] = None


class SpecializationCreate(SpecializationBase):
    field_id: Optional[UUID] = None


class SpecializationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    real_world_example: Optional[str] = None
    job_roles: Optional[List[str]] = None
    salary_range: Optional[str] = None
    prerequisites: Optional[str] = None
    status: Optional[str] = None
    field_id: Optional[UUID] = None


class SpecializationResponse(SpecializationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime