from sqlalchemy import String, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Boolean, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=True), primary_key=True,
                                    nullable=False, server_default=func.gen_random_uuid())
    firebase_user_id: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(
        timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_type: Mapped[str] = mapped_column(
        String(50), default="person", nullable=False)
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} name={self.name} active={self.is_active}>"
