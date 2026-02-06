import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ActionSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    amount: float | None = None
    date: datetime
    image_urls: list[str] = Field(default_factory=list, description="At least one image URL")
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class ActionCreateSchema(BaseModel):
    action_type: str
    amount: float
    image_urls: list[str] | None = Field(
        default=None, description="Optional list of image URLs"
    )
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    date: datetime | None = None


class ActionPhotosUpdate(BaseModel):
    image_urls: list[str] = Field(default_factory=list, description="List of image URLs")
