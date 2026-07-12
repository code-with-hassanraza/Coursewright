from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FieldBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon_key: Optional[str] = None


class FieldCreate(FieldBase):
    pass


class FieldResponse(FieldBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    