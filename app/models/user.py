from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from sqlalchemy import DateTime, Boolean, func


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=True), primary_key=True,
                                    unique=True, nullable=False, server_default=func.gen_random_uuid())
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

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} name={self.name} active={self.is_active}>"
