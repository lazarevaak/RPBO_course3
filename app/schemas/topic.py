# schemas/topic.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, constr


class TopicCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)  # нельзя пустую строку
    deadline: Optional[date] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    deadline: Optional[date] = None
    progress: int

    class Config:
        orm_mode = True


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)  # проверка диапазона 0..100
