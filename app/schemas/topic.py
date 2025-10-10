# schemas/topic.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, constr


class TopicCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)
    deadline: Optional[date] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    deadline: Optional[date] = None
    progress: int

    model_config = ConfigDict(from_attributes=True)


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)
