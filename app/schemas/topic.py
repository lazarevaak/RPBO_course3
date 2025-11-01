from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
Currency = Annotated[str, StringConstraints(min_length=1, max_length=3)]


class TopicCreate(BaseModel):
    title: Title
    deadline: Optional[date] = None

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("Deadline cannot be in the past")
        return v


class TopicResponse(BaseModel):
    id: int
    title: str
    deadline: Optional[date] = None
    progress: int

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)


class Payment(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: Currency
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def normalize_utc(cls, v: datetime) -> datetime:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
