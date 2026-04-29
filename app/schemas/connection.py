import uuid
from datetime import datetime

from pydantic import BaseModel

# ── Connection types ──────────────────────────────────────────────────────────


def infer_connection_type(from_type: str, to_type: str) -> str:
    """Derive the semantic connection type from the entity types."""
    if to_type == "initiative":
        return "contribution"
    if from_type == "directory_of_good" and to_type == "directory_of_good":
        return "partnership"
    # user → directory_of_good
    return "follow"


# ── Schemas ───────────────────────────────────────────────────────────────────


class ConnectionCreateSchema(BaseModel):
    created_by: uuid.UUID
    from_type: str  # "user" | "directory_of_good"
    from_id: uuid.UUID
    to_type: str  # "initiative" | "directory_of_good"
    to_id: uuid.UUID


class ConnectionSchema(BaseModel):
    id: uuid.UUID
    created_by: uuid.UUID
    from_type: str
    from_id: uuid.UUID
    to_type: str
    to_id: uuid.UUID
    connection_type: str  # "follow" | "partnership" | "contribution"
    created_at: datetime

    class Config:
        from_attributes = True


class PreviewUserSchema(BaseModel):
    id: uuid.UUID
    name: str | None = None
    photo_url: str | None = None

    class Config:
        from_attributes = True


class ConnectionWithUserSchema(ConnectionSchema):
    """Connection with the creator's basic profile, used in per-entity listings."""

    user: PreviewUserSchema | None = None


class ConnectionSummarySchema(BaseModel):
    """Aggregated connection info for one entity — used by the bulk summary endpoint."""

    to_id: uuid.UUID
    total_count: int
    user_count: int
    org_count: int
    preview_users: list[PreviewUserSchema]
    org_ids: list[uuid.UUID]
