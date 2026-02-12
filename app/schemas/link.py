import uuid

from pydantic import BaseModel


class LinkSchema(BaseModel):
    """Link entity response schema."""

    id: uuid.UUID
    project_id: uuid.UUID
    initiative_id: uuid.UUID

    model_config = {"from_attributes": True}


class LinkCreateSchema(BaseModel):
    """Create a link between a project and an initiative."""

    project_id: uuid.UUID
    initiative_id: uuid.UUID


class LinkUpdateSchema(BaseModel):
    """Update a link (change project or initiative)."""

    project_id: uuid.UUID | None = None
    initiative_id: uuid.UUID | None = None
