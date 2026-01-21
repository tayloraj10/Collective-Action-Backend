from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ActionSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    amount: Optional[float] = None
    date: datetime
    image_url: Optional[str] = None
    linked_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ActionCreateSchema(BaseModel):
    action_type: str
    amount: Optional[float] = None
    image_url: Optional[str] = None
    linked_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
