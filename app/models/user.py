from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.directory_of_good import DirectoryOfGood


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, server_default=func.gen_random_uuid()
    )
    firebase_user_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_type: Mapped[str] = mapped_column(String(50), default="person", nullable=False)
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # When this user is linked to a Directory of Good entry
    directory_of_good_entry: Mapped["DirectoryOfGood | None"] = relationship(
        "DirectoryOfGood", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} name={self.name} active={self.is_active}>"
