import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    # The user who created/authorized this connection (always a user).
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # What is connecting: "user" or "directory_of_good"
    from_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    # What it connects to: "initiative" or "directory_of_good"
    to_type: Mapped[str] = mapped_column(String(50), nullable=False)
    to_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)

    # Semantic type — auto-inferred from from_type/to_type:
    #   user  → dog        = "follow"
    #   dog   → dog        = "partnership"
    #   user  → initiative = "contribution"
    #   dog   → initiative = "contribution"
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False, default="contribution")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])  # noqa: F821

    __table_args__ = (
        UniqueConstraint("from_type", "from_id", "to_type", "to_id", name="uq_connection_from_to"),
    )

    def __repr__(self) -> str:
        return (
            f"<Connection id={self.id} "
            f"{self.from_type}:{self.from_id} -> {self.to_type}:{self.to_id}>"
        )
