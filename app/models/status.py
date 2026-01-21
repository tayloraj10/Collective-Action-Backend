import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status_type: Mapped[str] = mapped_column(String(100), nullable=False)
