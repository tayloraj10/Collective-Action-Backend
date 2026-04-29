from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SocialLinksSchema(BaseModel):
    youtube: str | None = None
    instagram: str | None = None
    tiktok: str | None = None
    website: str | None = None


class LocationSchema(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None


class UserType(StrEnum):
    PERSON = "person"
    GROUP = "group"


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None
    photo_url: str | None = None
    user_type: UserType | None = None
    is_active: bool | None = None
    admin: bool | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
    firebase_user_id: str | None = None


class UserUpdate(BaseModel):
    """Schema for PATCH updates. Excludes photo_url, firebase_user_id, is_active."""

    email: EmailStr | None = None
    name: str | None = None
    user_type: UserType | None = None
    admin: bool | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None


class UserPhotoUpdate(BaseModel):
    photo_url: str


class UserSchema(BaseModel):
    id: UUID | None = None
    email: EmailStr | None = None
    name: str | None = None
    photo_url: str | None = None
    user_type: UserType | None = None
    is_active: bool | None = None
    admin: bool | None = None
    location: LocationSchema | None = None
    social_links: SocialLinksSchema | None = None
    firebase_user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MapCampaignStatsSchema(BaseModel):
    """Stats for a single map campaign the user has submitted to."""

    campaign_id: UUID | None = None
    campaign_name: str = "Unknown campaign"
    submission_count: int = 0
    cleanup_count: int = 0
    trash_report_count: int = 0
    total_bags: int = 0
    total_pounds: float = 0.0


class UserStatsSchema(BaseModel):
    user_id: UUID
    # Map impact
    map_submission_count: int = 0
    cleanup_count: int = 0
    trash_report_count: int = 0
    total_small_bags: int = 0
    total_large_bags: int = 0
    total_bags: int = 0
    total_pounds: float = 0.0
    # Initiative contributions (Action records of type "Initiative")
    initiative_action_count: int = 0  # number of logged contributions
    initiatives_participated: int = 0  # distinct initiatives acted on
    # Per-campaign map breakdown
    map_campaign_breakdown: list[MapCampaignStatsSchema] = []
    # Breakdown of all actions by type — keys are the action_type strings
    action_type_counts: dict[str, int] = {}
    # Outgoing connections (things this user has connected to)
    follows_count: int = 0  # orgs they follow
    contributions_count: int = 0  # initiatives they've connected to
    # Org-level stats (only populated if user owns a DoG entry)
    org_id: UUID | None = None
    org_name: str | None = None
    org_followers_count: int = 0
    org_partnerships_count: int = 0
    org_initiative_connections: int = 0
    # Activity timeline
    total_actions: int = 0
    first_action_date: datetime | None = None
    last_action_date: datetime | None = None
