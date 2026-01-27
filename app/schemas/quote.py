from uuid import UUID
from pydantic import BaseModel


class QuoteSchema(BaseModel):
    id: UUID
    text: str
    translation: str | None = None
    active: bool

    class Config:
        from_attributes = True


class QuoteCreateSchema(BaseModel):
    text: str
    translation: str | None = None
    active: bool = True
