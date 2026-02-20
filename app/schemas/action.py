import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ActionSchema(BaseModel):
    id: uuid.UUID
    action_type: str
    amount: float | None = None
    date: datetime
    image_urls: list[str] = Field(default_factory=list, description="List of image URLs")
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    latitude: float | None = None
    longitude: float | None = None
    event_data: dict | None = None

    @field_validator("image_urls", mode="before")
    @classmethod
    def image_urls_none_to_list(cls, v: list[str] | None) -> list[str]:
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True


class ActionCreateSchema(BaseModel):
    action_type: str
    amount: float
    image_urls: list[str] | None = Field(default=None, description="Optional list of image URLs")
    linked_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    date: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    event_data: dict | None = None


class ActionPhotosUpdate(BaseModel):
    image_urls: list[str] = Field(default_factory=list, description="List of image URLs")
