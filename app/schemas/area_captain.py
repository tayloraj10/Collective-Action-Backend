import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.map_area import MapAreaSchema


class AreaCaptainSchema(BaseModel):
    id: uuid.UUID
    map_area_id: uuid.UUID
    captain_user_id: uuid.UUID
    assigned_by_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    area: MapAreaSchema | None = None

    class Config:
        from_attributes = True


class AreaCaptainAssignSchema(BaseModel):
    map_area_id: uuid.UUID
    captain_user_id: uuid.UUID
    acting_user_id: uuid.UUID


class AreaCaptainRemoveSchema(BaseModel):
    acting_user_id: uuid.UUID
