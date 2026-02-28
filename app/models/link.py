import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Link(Base):
    """Links entities; project_id, initiative_id, and map_campaign_id are all optional."""

    __tablename__ = "links"
    __table_args__ = (
        UniqueConstraint("project_id", "initiative_id", name="uq_link"),
        UniqueConstraint("project_id", "map_campaign_id", name="uq_link_project_map_campaign"),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    initiative_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=True
    )
    map_campaign_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("map_campaigns.id", ondelete="CASCADE"), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<Link id={self.id} project_id={self.project_id} "
            f"initiative_id={self.initiative_id} map_campaign_id={self.map_campaign_id}>"
        )
