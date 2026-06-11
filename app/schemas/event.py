from uuid import uuid4

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
