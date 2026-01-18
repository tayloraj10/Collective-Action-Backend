from sqlalchemy import ForeignKey, String, Boolean, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid


class Initiative(Base):
    __tablename__ = "initiatives"

    id: Mapped[str] = mapped_column(Uuid(
        as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    goal: Mapped[int] = mapped_column(Integer, nullable=True)
    complete: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String(512), nullable=True)
    priority: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    status_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("statuses.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Initiative id={self.id} title={self.title} action={self.action}>"
