import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class MapAreaTypeEnum(StrEnum):
    """Granularity of a map area — boroughs today, neighborhoods/cities/towns later."""

    borough = "borough"
    neighborhood = "neighborhood"
    city = "city"
    town = "town"
    region = "region"
    custom = "custom"


class MapAreaBoundsSchema(BaseModel):
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class MapAreaSchema(BaseModel):
    id: uuid.UUID
    map_campaign_id: uuid.UUID
    name: str
    area_type: str
    slug: str | None = None
    parent_area_id: uuid.UUID | None = None
    bounds: MapAreaBoundsSchema | None = None
    sort_order: int = 0
    active: bool = True

    class Config:
        from_attributes = True


class MapAreaCreateSchema(BaseModel):
    map_campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    area_type: MapAreaTypeEnum
    slug: str | None = Field(default=None, max_length=100)
    parent_area_id: uuid.UUID | None = None
    bounds: MapAreaBoundsSchema | None = None
    sort_order: int = 0
    acting_user_id: uuid.UUID
