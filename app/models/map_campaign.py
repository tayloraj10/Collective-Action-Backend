import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MapCampaign(Base):
    """Campaign that drives user actions on a map (e.g. Cleanup Map, Zip Code Map)."""

    __tablename__ = "map_campaigns"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    map_campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("statuses.id"), nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MapCampaign id={self.id} title={self.title} type={self.map_campaign_type}>"
