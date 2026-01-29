from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SocialLinksSchema(BaseModel):
    youtube: str | None = None
    instagram: str | None = None
    tiktok: str | None = None
    website: str | None = None


class LocationSchema(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None


class UserType(str, Enum):
    PERSON = "person"
    GROUP = "group"


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None
    photo_url: str | None = None
    user_type: UserType | None = None
    is_active: bool | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
    firebase_user_id: str | None = None


class UserSchema(BaseModel):
    id: UUID | None = None
    email: EmailStr | None = None
    name: str | None = None
    photo_url: str | None = None
    user_type: UserType | None = None
    is_active: bool | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
    firebase_user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
