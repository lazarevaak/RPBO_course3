# schemas/topic.py
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, constr, field_validator


class TopicCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=50)
    deadline: Optional[date] = None

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, v: Optional[date]):
        if v and v < date.today():
            raise ValueError("Deadline cannot be in the past")
        return v


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)


class Payment(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: constr(min_length=3, max_length=3)
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def normalize_utc(cls, v: datetime):
        # нормализация к UTC
        return v.astimezone(timezone.utc).replace(tzinfo=None)
