import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


ALLOWED_MEMBER_ROLES = ("members", "owners", "developers")


class MemberIdsByRole(BaseModel):
    """Only 'members', 'owners', and 'developers' are allowed."""

    model_config = {"extra": "forbid"}

    members: list[uuid.UUID] = Field(default_factory=list)
    owners: list[uuid.UUID] = Field(default_factory=list)
    developers: list[uuid.UUID] = Field(default_factory=list)


ProjectMemberRole = Literal["members", "owners", "developers"]


class AddProjectMemberSchema(BaseModel):
    """Body for adding a user to a project."""

    user_id: uuid.UUID
    role: ProjectMemberRole


# --- Project role (table) ---


class ProjectRoleSchema(BaseModel):
    """Project role response."""

    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ProjectRoleCreateSchema(BaseModel):
    """Create a new project role."""

    name: str


class ProjectRoleUpdateSchema(BaseModel):
    """Update a project role."""

    name: str


# --- Project member (table) ---


class ProjectMemberSchema(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID

    model_config = {"from_attributes": True}


# --- Project step (table) ---


class ProjectStepSchema(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    order: int = 0
    title: str
    description: str | None = None
    completed: bool = False
    status_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class ProjectStepCreateSchema(BaseModel):
    """Payload for creating a step (no id)."""

    order: int = 0
    title: str
    description: str | None = None
    completed: bool = False
    status_id: uuid.UUID | None = None


class ProjectStepUpdateSchema(BaseModel):
    """Payload for updating a step."""

    order: int | None = None
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    status_id: uuid.UUID | None = None


# --- Project link (table: one optional column per link type) ---


class ProjectLinkSchema(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    initiative_id: uuid.UUID

    model_config = {"from_attributes": True}


class ProjectLinkCreateSchema(BaseModel):
    """Link a project to an initiative."""

    initiative_id: uuid.UUID


# --- Project (response: full data with members, steps, links) ---


class ProjectSchema(BaseModel):
    """Project with nested members, steps, and links (for GET responses)."""

    id: uuid.UUID
    name: str
    description: str | None = None
    category_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    creator_id: uuid.UUID
    active: bool = True
    members: MemberIdsByRole = Field(default_factory=MemberIdsByRole)
    steps: list[ProjectStepSchema] = Field(default_factory=list)
    links: list[ProjectLinkSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Project create / update (request bodies) ---


class ProjectCreateSchema(BaseModel):
    name: str
    description: str | None = None
    category_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    creator_id: uuid.UUID
    active: bool = True
    members: MemberIdsByRole = Field(default_factory=MemberIdsByRole)
    steps: list[ProjectStepCreateSchema] = Field(default_factory=list)


class ProjectUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    active: bool | None = None
    members: MemberIdsByRole | None = None
    steps: list[ProjectStepCreateSchema] | None = None
