import datetime
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    linked_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    image_urls: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    # Map event location (for actions linked to map campaigns)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    # Optional type-specific payload (e.g. map events; validated by event_data schemas)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    # User ids (users.id) who liked this action, newest-like first. Stored as JSON list of strings.
    like_user_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resolved_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_by_action_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("actions.id", ondelete="SET NULL"), nullable=True
    )
    source_trash_report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("actions.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Action id={self.id} action_type={self.action_type} user_id={self.user_id}>"
