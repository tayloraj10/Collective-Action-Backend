from pydantic import BaseModel
from typing import Optional
import uuid


class InitiativeSchema(BaseModel):
    id: uuid.UUID
    title: str
    action: str
    category_id: Optional[uuid.UUID] = None
    goal: Optional[int] = None
    complete: Optional[int] = None
    link: Optional[str] = None
    priority: bool = False
    status_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class InitiativeCreateSchema(BaseModel):
    title: str
    action: str
    category_id: Optional[str] = None
    goal: Optional[int] = None
    link: Optional[str] = None
    priority: bool = False
    status_id: Optional[str] = None
