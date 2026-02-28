from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.initiative import Initiative
from app.models.link import Link
from app.models.status import Status
from app.models.user import User
from app.schemas.initiative import InitiativeCreateSchema, InitiativeSchema
from app.schemas.status import StatusTypeEnum, StatusValuesEnum

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


@router.post("/", response_model=InitiativeSchema)
def create_initiative(initiative: InitiativeCreateSchema, db: Session = Depends(get_db)):
    # Ensure created_by references an existing user
    creator = db.query(User).filter(User.id == initiative.created_by).first()
    if not creator:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {initiative.created_by} not found; cannot set created_by.",
        )
    db_initiative = Initiative(**initiative.model_dump())
    db.add(db_initiative)
    db.commit()
    db.refresh(db_initiative)
    return db_initiative


@router.get("/", response_model=list[InitiativeSchema])
def list_initiatives(db: Session = Depends(get_db)):
    return db.query(Initiative).all()


@router.get("/active", response_model=list[InitiativeSchema])
def list_active_initiatives(db: Session = Depends(get_db)):
    active_status = (
        db.query(Status)
        .filter(
            Status.name == StatusValuesEnum.active,
            Status.status_type == StatusTypeEnum.status,
        )
        .first()
    )
    if not active_status:
        return []
    return (
        db.query(Initiative)
        .filter(Initiative.status_id == active_status.id)
        .order_by(Initiative.priority.desc(), func.coalesce(Initiative.complete, 0).desc())
        .all()
    )


@router.get("/creator/{user_id}", response_model=list[InitiativeSchema])
def list_initiatives_by_creator(user_id: UUID, db: Session = Depends(get_db)):
    """Get all initiatives created by a specific user."""
    return db.query(Initiative).filter(Initiative.created_by == user_id).all()


@router.get("/featured", response_model=list[InitiativeSchema])
def get_featured_initiatives(db: Session = Depends(get_db)):
    # 1. Fetch initiatives with priority=True, sorted by complete (desc)
    priority_initiatives = (
        db.query(Initiative)
        .filter_by(priority=True)
        .order_by(func.coalesce(Initiative.complete, 0).desc())
        .all()
    )
    featured = {i.id: i for i in priority_initiatives}

    # 2. Fetch initiatives with recent activity (from actions)
    recent_cutoff = datetime.now(UTC) - timedelta(days=7)
    recent_action_initiative_ids = (
        db.query(Action.linked_id)
        .filter(Action.date >= recent_cutoff)
        .filter(Action.linked_id is not None)
        .distinct()
        .all()
    )
    for (initiative_id,) in recent_action_initiative_ids:
        if initiative_id and initiative_id not in featured:
            initiative = db.query(Initiative).filter_by(id=initiative_id).first()
            if initiative:
                featured[initiative_id] = initiative

    # 3. If fewer than 4, fill with most complete (assuming 'complete' is a column)
    if len(featured) < 4:
        needed = 4 - len(featured)
        from sqlalchemy import nullslast

        more = (
            db.query(Initiative)
            .filter(~Initiative.id.in_(featured.keys()))
            .order_by(nullslast(Initiative.complete.desc()))
            .limit(needed)
            .all()
        )
        for i in more:
            featured[i.id] = i

    return list(featured.values())


@router.get("/by-ids", response_model=list[InitiativeSchema])
def get_initiatives_by_ids(
    initiative_ids: list[UUID] = Query(..., description="List of initiative IDs"),
    db: Session = Depends(get_db),
):
    initiatives = db.query(Initiative).filter(Initiative.id.in_(initiative_ids)).all()
    if not initiatives:
        raise HTTPException(status_code=404, detail="No initiatives found for the given IDs")
    return initiatives


@router.get("/{initiative_id}", response_model=InitiativeSchema)
def get_initiative(
    initiative_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single initiative by ID (includes created_by)."""
    initiative = db.query(Initiative).filter(Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return initiative


@router.delete("/{initiative_id}", status_code=204)
def delete_initiative(initiative_id: UUID, db: Session = Depends(get_db)):
    """Delete an initiative. Fails with 409 if any link references this initiative."""
    initiative = db.query(Initiative).filter(Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    link_count = db.query(Link).filter(Link.initiative_id == initiative_id).count()
    if link_count:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot delete initiative: it is referenced by one or more links. "
                "Remove or update the initiative_id from those links first."
            ),
        )
    db.delete(initiative)
    db.commit()
    return None
