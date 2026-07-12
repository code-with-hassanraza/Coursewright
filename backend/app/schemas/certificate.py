from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    specialization_id: UUID
    certificate_code: str
    issued_at: datetime


class CertificateGenerate(BaseModel):
    specialization_id: UUID


class CertificateVerify(BaseModel):
    certificate_code: str
    user_id: UUID
    specialization_id: UUID
    issued_at: datetime