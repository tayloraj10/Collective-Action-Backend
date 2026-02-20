from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import LocationSchema, SocialLinksSchema


class DirectoryOfGoodSchema(BaseModel):
    id: UUID | None = None
    name: str
    focus: str | None = None
    category_id: UUID | None = None
    image_url: str | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
    user_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DirectoryOfGoodCreate(BaseModel):
    name: str
    focus: str | None = None
    category_id: UUID | None = None
    image_url: str | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None


class DirectoryOfGoodUpdate(BaseModel):
    name: str | None = None
    focus: str | None = None
    category_id: UUID | None = None
    image_url: str | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
