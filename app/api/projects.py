from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.link import Link
from app.models.project import Project, ProjectMember, ProjectRole, ProjectStep
from app.schemas.project import (
    ALLOWED_MEMBER_ROLES,
    AddProjectMemberSchema,
    MemberIdsByRole,
    ProjectCreateSchema,
    ProjectLinkSchema,
    ProjectRoleCreateSchema,
    ProjectRoleSchema,
    ProjectRoleUpdateSchema,
    ProjectSchema,
    ProjectStepCreateSchema,
    ProjectStepSchema,
    ProjectStepUpdateSchema,
    ProjectUpdateSchema,
)

router = APIRouter(prefix="/projects", tags=["projects"])
roles_router = APIRouter(prefix="/project-roles", tags=["project-roles"])


def _project_query_with_relations(db: Session):
    """Query projects with members and steps loaded."""
    return db.query(Project).options(
        joinedload(Project.project_members).joinedload(ProjectMember.role),
        joinedload(Project.project_steps),
    )


def _get_role_id_by_name(db: Session, role_name: str) -> UUID:
    """Get role ID by role name. Raises 404 if not found."""
    role = db.query(ProjectRole).filter(ProjectRole.name == role_name).first()
    if not role:
        raise HTTPException(status_code=500, detail=f"Role '{role_name}' not found in database")
    return role.id


def _build_members_from_relations(project_members: list) -> MemberIdsByRole:
    members = MemberIdsByRole()
    for pm in project_members or []:
        role_name = pm.role.name  # Access role name from relationship
        if role_name == "owner":
            role_key = "owners"
        elif role_name == "developer":
            role_key = "developers"
        else:
            role_key = "members"
        getattr(members, role_key).append(pm.user_id)
    return members


def _project_to_schema(project: Project, db: Session) -> ProjectSchema:
    """Build ProjectSchema from ORM project with relations loaded."""
    # Load links separately (no relationship on Project)
    links = db.query(Link).filter(Link.project_id == project.id).all()
    return ProjectSchema(
        id=project.id,
        name=project.name,
        description=project.description,
        category_id=project.category_id,
        status_id=project.status_id,
        creator_id=project.creator_id,
        active=project.active,
        members=_build_members_from_relations(project.project_members),
        steps=[ProjectStepSchema.model_validate(s) for s in (project.project_steps or [])],
        links=[ProjectLinkSchema.model_validate(l) for l in links],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/", response_model=ProjectSchema)
def create_project(project: ProjectCreateSchema, db: Session = Depends(get_db)):
    # Create project (flat fields only)
    db_project = Project(
        name=project.name,
        description=project.description,
        category_id=project.category_id,
        status_id=project.status_id,
        creator_id=project.creator_id,
        active=project.active,
    )
    db.add(db_project)
    db.flush()  # get db_project.id

    # Create project_members
    for role_key in ALLOWED_MEMBER_ROLES:
        role_name = "owner" if role_key == "owners" else ("developer" if role_key == "developers" else "member")
        role_id = _get_role_id_by_name(db, role_name)
        for user_id in getattr(project.members, role_key):
            db.add(ProjectMember(project_id=db_project.id, user_id=user_id, role_id=role_id))
    # Create project_steps
    for s in project.steps:
        db.add(
            ProjectStep(
                project_id=db_project.id,
                order=s.order,
                title=s.title,
                description=s.description,
                completed=s.completed,
                status_id=s.status_id,
            )
        )

    db.commit()
    db_project = _project_query_with_relations(db).filter(Project.id == db_project.id).first()
    return _project_to_schema(db_project, db)


@router.get("/", response_model=list[ProjectSchema])
def list_projects(db: Session = Depends(get_db)):
    projects = _project_query_with_relations(db).all()
    return [_project_to_schema(p, db) for p in projects]


@router.get("/active", response_model=list[ProjectSchema])
def list_active_projects(db: Session = Depends(get_db)):
    projects = _project_query_with_relations(db).filter(Project.active.is_(True)).all()
    return [_project_to_schema(p, db) for p in projects]


@router.get("/creator/{creator_id}", response_model=list[ProjectSchema])
def list_projects_by_creator(creator_id: UUID, db: Session = Depends(get_db)):
    """Get all projects created by a specific user."""
    projects = _project_query_with_relations(db).filter(Project.creator_id == creator_id).all()
    return [_project_to_schema(p, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_schema(db_project, db)


@router.patch("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: UUID,
    project: ProjectUpdateSchema,
    db: Session = Depends(get_db),
):
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    if "members" in update_data:
        # Replace members: delete existing, add new
        for pm in list(db_project.project_members):
            db.delete(pm)
        members = update_data.pop("members")
        for role_key in ALLOWED_MEMBER_ROLES:
            role_name = "owner" if role_key == "owners" else ("developer" if role_key == "developers" else "member")
            role_id = _get_role_id_by_name(db, role_name)
            for user_id in members.get(role_key, []):
                db.add(ProjectMember(project_id=db_project.id, user_id=user_id, role_id=role_id))
    if "steps" in update_data:
        for s in list(db_project.project_steps):
            db.delete(s)
        for s in update_data.pop("steps"):
            db.add(
                ProjectStep(
                    project_id=db_project.id,
                    order=s["order"],
                    title=s["title"],
                    description=s.get("description"),
                    completed=s.get("completed", False),
                    status_id=s.get("status_id"),
                )
            )

    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


@router.delete("/{project_id}", response_model=ProjectSchema)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    out = _project_to_schema(db_project, db)
    db.delete(db_project)
    db.commit()
    return out


@router.post("/{project_id}/members", response_model=ProjectSchema)
def add_member_to_project(
    project_id: UUID,
    body: AddProjectMemberSchema,
    db: Session = Depends(get_db),
):
    """Add a user to a project in the given role (members, owners, or developers)."""
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    role_name = "owner" if body.role == "owners" else ("developer" if body.role == "developers" else "member")
    role_id = _get_role_id_by_name(db, role_name)
    existing = next(
        (pm for pm in db_project.project_members if str(pm.user_id) == str(body.user_id)),
        None,
    )
    if existing:
        existing.role_id = role_id
    else:
        db.add(ProjectMember(project_id=db_project.id, user_id=body.user_id, role_id=role_id))
    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectSchema)
def remove_member_from_project(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Remove a user from a project."""
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    to_remove = [pm for pm in db_project.project_members if str(pm.user_id) == str(user_id)]
    for pm in to_remove:
        db.delete(pm)
    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


@router.post("/{project_id}/steps", response_model=ProjectSchema)
def add_step_to_project(
    project_id: UUID,
    body: ProjectStepCreateSchema,
    db: Session = Depends(get_db),
):
    """Add a step to a project."""
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_step = ProjectStep(
        project_id=project_id,
        order=body.order,
        title=body.title,
        description=body.description,
        completed=body.completed,
        status_id=body.status_id,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


@router.patch("/{project_id}/steps/{step_id}", response_model=ProjectSchema)
def update_project_step(
    project_id: UUID,
    step_id: UUID,
    body: ProjectStepUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update a specific step in a project."""
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_step = db.query(ProjectStep).filter(
        ProjectStep.id == step_id,
        ProjectStep.project_id == project_id
    ).first()
    if not db_step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_step, key, value)
    
    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


@router.delete("/{project_id}/steps/{step_id}", response_model=ProjectSchema)
def delete_project_step(
    project_id: UUID,
    step_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a specific step from a project."""
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_step = db.query(ProjectStep).filter(
        ProjectStep.id == step_id,
        ProjectStep.project_id == project_id
    ).first()
    if not db_step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    db.delete(db_step)
    db.commit()
    db.refresh(db_project)
    db_project = _project_query_with_relations(db).filter(Project.id == project_id).first()
    return _project_to_schema(db_project, db)


# === Project Roles Endpoints ===


@roles_router.post("/", response_model=ProjectRoleSchema)
def create_project_role(role: ProjectRoleCreateSchema, db: Session = Depends(get_db)):
    """Create a new project role."""
    # Check if role name already exists
    existing = db.query(ProjectRole).filter(ProjectRole.name == role.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Role '{role.name}' already exists")
    
    db_role = ProjectRole(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@roles_router.get("/", response_model=list[ProjectRoleSchema])
def list_project_roles(db: Session = Depends(get_db)):
    """List all project roles."""
    roles = db.query(ProjectRole).all()
    return roles


@roles_router.get("/{role_id}", response_model=ProjectRoleSchema)
def get_project_role(role_id: UUID, db: Session = Depends(get_db)):
    """Get a specific project role."""
    db_role = db.query(ProjectRole).filter(ProjectRole.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role


@roles_router.patch("/{role_id}", response_model=ProjectRoleSchema)
def update_project_role(
    role_id: UUID,
    role: ProjectRoleUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update a project role."""
    db_role = db.query(ProjectRole).filter(ProjectRole.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if new name conflicts with existing role
    if role.name != db_role.name:
        existing = db.query(ProjectRole).filter(ProjectRole.name == role.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Role '{role.name}' already exists")
    
    db_role.name = role.name
    db.commit()
    db.refresh(db_role)
    return db_role


@roles_router.delete("/{role_id}", response_model=ProjectRoleSchema)
def delete_project_role(role_id: UUID, db: Session = Depends(get_db)):
    """Delete a project role."""
    db_role = db.query(ProjectRole).filter(ProjectRole.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if role is in use
    in_use = db.query(ProjectMember).filter(ProjectMember.role_id == role_id).first()
    if in_use:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role '{db_role.name}' - it is currently assigned to project members"
        )
    
    out = ProjectRoleSchema.model_validate(db_role)
    db.delete(db_role)
    db.commit()
    return out
