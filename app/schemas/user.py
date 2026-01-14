from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, EmailStr, ConfigDict


class UserType(str, Enum):
    PERSON = "person"
    GROUP = "group"


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    photo_url: str | None = None


# ...existing code...


class UserSchema(BaseModel):
    id: UUID | None = None
    email: EmailStr | None = None
    name: str | None = None
    photo_url: str | None = None
    user_type: UserType | None = None
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
