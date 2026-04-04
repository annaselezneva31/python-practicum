from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    text: str
    source: str
    created_at: datetime


class FactListResponse(BaseModel):
    count: int
    items: list[FactResponse]
