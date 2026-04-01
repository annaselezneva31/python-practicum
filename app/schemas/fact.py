from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FactResponse(BaseModel):
    id: UUID
    text: str
    source: str
    created_at: datetime


class FactListResponse(BaseModel):
    count: int
    items: list[FactResponse]
