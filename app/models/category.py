
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid
import uuid


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(Uuid(
        as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
