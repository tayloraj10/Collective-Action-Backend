import uuid

from pydantic import BaseModel


class InitiativeSchema(BaseModel):
    id: uuid.UUID
    title: str
    action: str
    category_id: uuid.UUID | None = None
    goal: int | None = None
    complete: int | None = None
    link: str | None = None
    priority: bool = False
    status_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class InitiativeCreateSchema(BaseModel):
    title: str
    action: str
    category_id: str | None = None
    goal: int | None = None
    link: str | None = None
    priority: bool = False
    status_id: str | None = None
