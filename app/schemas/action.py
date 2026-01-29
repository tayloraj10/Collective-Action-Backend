import uuid
from datetime import datetime

from pydantic import BaseModel


class ActionSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    amount: float | None = None
    date: datetime
    image_url: str | None = None
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class ActionCreateSchema(BaseModel):
    action_type: str
    amount: float
    image_url: str | None = None
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    date: datetime | None = None
