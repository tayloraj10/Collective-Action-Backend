from pydantic import BaseModel
from uuid import UUID
from enum import Enum


# class StatusValuesEnum(str, Enum):
#     in_progress = "In Progress"
#     completed = "Completed"
#     active = "Active"
#     inactive = "Inactive"


class StatusSchema(BaseModel):
    id: UUID | None = None
    name: str


class StatusCreate(BaseModel):
    name: str
