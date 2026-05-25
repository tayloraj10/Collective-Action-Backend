import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.map_area import MapAreaSchema


class MapHotspotSchema(BaseModel):
    id: uuid.UUID
    map_campaign_id: uuid.UUID
    map_area_id: uuid.UUID
    title: str
    description: str | None = None
    latitude: float
    longitude: float
    created_by: uuid.UUID
    active: bool = True
    created_at: datetime
    updated_at: datetime
    area: MapAreaSchema | None = None

    class Config:
        from_attributes = True


class MapHotspotCreateSchema(BaseModel):
    map_campaign_id: uuid.UUID
    map_area_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    latitude: float
    longitude: float
    created_by: uuid.UUID


class MapHotspotUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    active: bool | None = None
    acting_user_id: uuid.UUID
