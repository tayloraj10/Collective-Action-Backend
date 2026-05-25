import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MapArea(Base):
    """A geographic or administrative area within a map campaign.

    Examples: NYC borough, a neighborhood, a whole city/town, or a custom region.
    """

    __tablename__ = "map_areas"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    map_campaign_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("map_campaigns.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_type: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_area_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("map_areas.id"), nullable=True
    )
    bounds: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MapArea id={self.id} name={self.name} type={self.area_type}>"
