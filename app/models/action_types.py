
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid
import uuid


class ActionTypes(Base):
    __tablename__ = "action_types"

    id: Mapped[str] = mapped_column(Uuid(
        as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
