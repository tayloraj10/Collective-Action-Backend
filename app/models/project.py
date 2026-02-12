import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    status_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("statuses.id"), nullable=True
    )
    creator_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project_members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    project_steps: Mapped[list["ProjectStep"]] = relationship(
        "ProjectStep",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectStep.order",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name} active={self.active}>"


class ProjectRole(Base):
    """Project member roles: owner, developer, member."""

    __tablename__ = "project_roles"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ProjectRole id={self.id} name={self.name}>"


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("project_roles.id"), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="project_members")
    role = relationship("ProjectRole")

    def __repr__(self) -> str:
        return (
            f"<ProjectMember project_id={self.project_id} "
            f"user_id={self.user_id} role_id={self.role_id}>"
        )


class ProjectStep(Base):
    __tablename__ = "project_steps"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("statuses.id"), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="project_steps")

    def __repr__(self) -> str:
        return f"<ProjectStep id={self.id} project_id={self.project_id} order={self.order}>"
