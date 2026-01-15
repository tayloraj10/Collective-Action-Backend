from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ActionSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    amount: Optional[int] = None
    date: datetime
    image_url: Optional[str] = None
    initiative_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    extra_data: Optional[dict] = None

    class Config:
        from_attributes = True


class ActionCreateSchema(BaseModel):
    action_type: str
    amount: Optional[int] = None
    date: datetime
    image_url: Optional[str] = None
    initiative_id: Optional[str] = None
    user_id: str
    extra_data: Optional[dict] = None
