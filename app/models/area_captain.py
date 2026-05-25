import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AreaCaptain(Base):
    """Captain assignment for a map area. An area may have multiple captains."""

    __tablename__ = "area_captains"
    __table_args__ = (
        UniqueConstraint("map_area_id", "captain_user_id", name="uq_area_captain_area_user"),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    map_area_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("map_areas.id"), nullable=False
    )
    captain_user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_by_user_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AreaCaptain area={self.map_area_id} captain={self.captain_user_id}>"
