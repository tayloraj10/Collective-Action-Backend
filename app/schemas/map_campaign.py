import uuid
from enum import StrEnum

from pydantic import BaseModel


class MapCampaignTypeEnum(StrEnum):
    cleanup_map = "Cleanup Map"
    zip_code_map = "Zip Code Map"


class MapCampaignSchema(BaseModel):
    id: uuid.UUID
    title: str
    map_campaign_type: str
    purpose: str | None = None
    description: str | None = None
    link: str | None = None
    active: bool = True
    status_id: uuid.UUID | None = None
    created_by: uuid.UUID

    class Config:
        from_attributes = True


class MapCampaignCreateSchema(BaseModel):
    """Matches MapCampaign model fields (excluding id)."""

    title: str
    map_campaign_type: MapCampaignTypeEnum
    purpose: str | None = None
    description: str | None = None
    link: str | None = None
    active: bool = True
    status_id: uuid.UUID | None = None
    created_by: uuid.UUID
