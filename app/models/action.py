import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    linked_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Action id={self.id} action_type={self.action_type} user_id={self.user_id}>"
