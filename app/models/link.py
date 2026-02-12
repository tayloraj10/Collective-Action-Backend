import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Link(Base):
    """Links entities together (e.g. project to initiative)."""

    __tablename__ = "links"
    __table_args__ = (UniqueConstraint("project_id", "initiative_id", name="uq_link"),)

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    initiative_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Link id={self.id} project_id={self.project_id} initiative_id={self.initiative_id}>"
        )
