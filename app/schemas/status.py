from pydantic import BaseModel
from uuid import UUID
from enum import Enum


class StatusValuesEnum(str, Enum):
    in_progress = "In Progress"
    completed = "Completed"
    active = "Active"
    inactive = "Inactive"


class StatusTypeEnum(str, Enum):
    status = "Status"
    project_status = "Project Status"


class StatusSchema(BaseModel):
    id: UUID | None = None
    name: StatusValuesEnum
    status_type: StatusTypeEnum


class StatusCreate(BaseModel):
    name: StatusValuesEnum
    status_type: StatusTypeEnum
