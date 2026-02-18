from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class StatusValuesEnum(StrEnum):
    not_started = "Not Started"
    in_development = "In Development"
    in_progress = "In Progress"
    in_review = "In Review"
    blocked = "Blocked"
    completed = "Completed"
    active = "Active"
    inactive = "Inactive"


class StatusTypeEnum(StrEnum):
    status = "Status"
    project_status = "Project Status"
    step_status = "Step Status"


class StatusSchema(BaseModel):
    id: UUID | None = None
    name: StatusValuesEnum
    status_type: StatusTypeEnum


class StatusCreate(BaseModel):
    name: StatusValuesEnum
    status_type: StatusTypeEnum
