from pydantic import BaseModel, EmailStr, ConfigDict


class UserSchema(BaseModel):
    id: int | None = None
    email: EmailStr | None = None
    name: str | None = None
    photo_url: str | None = None
    user_type: str | None = None
    is_active: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
