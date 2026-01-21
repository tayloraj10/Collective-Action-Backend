from enum import Enum
from uuid import UUID

from pydantic import BaseModel


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
