import uuid

from pydantic import BaseModel


class LinkSchema(BaseModel):
    """Link entity response schema."""

    id: uuid.UUID
    project_id: uuid.UUID | None = None
    initiative_id: uuid.UUID | None = None
    map_campaign_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class LinkCreateSchema(BaseModel):
    """Create a link; any combination of project_id, initiative_id, map_campaign_id."""

    project_id: uuid.UUID | None = None
    initiative_id: uuid.UUID | None = None
    map_campaign_id: uuid.UUID | None = None


class LinkUpdateSchema(BaseModel):
    """Update a link (change project and/or target)."""

    project_id: uuid.UUID | None = None
    initiative_id: uuid.UUID | None = None
    map_campaign_id: uuid.UUID | None = None
