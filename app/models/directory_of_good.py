"""Directory of Good: people doing good in the world.

Entries can exist without a user account. When the person later creates an account,
link them by setting user_id. When building API responses, you can prefer the user's
location and social_links over the directory's when user_id is set.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Double, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DirectoryOfGood(Base):
    """A person or org in the directory doing good (e.g. trash cleanup, mutual aid)."""

    __tablename__ = "directory_of_good"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    focus: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stores a JSON list of category ID strings — supports multiple categories per entry.
    # Replaces the old single category_id FK.
    category_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location: same shape as LocationSchema (city, state, country).
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Social: same shape as SocialLinksSchema (youtube, instagram, tiktok, website).
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Geocoded coordinates — populated automatically from location.zip_code / location.city.
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)

    # Optional link to user account (when they sign up / claim this entry)
    user_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User | None"] = relationship("User", back_populates="directory_of_good_entry")

    def __repr__(self) -> str:
        return f"<DirectoryOfGood id={self.id} name={self.name} user_id={self.user_id}>"
