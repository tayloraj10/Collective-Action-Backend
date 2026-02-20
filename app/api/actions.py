from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.directory_of_good import DirectoryOfGood
from app.schemas.action import ActionCreateSchema, ActionPhotosUpdate, ActionSchema
from app.schemas.action_types import ActionTypeValuesEnum
from app.schemas.event_data import validate_event_data

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/", response_model=ActionSchema)
def create_action(action: ActionCreateSchema, db: Session = Depends(get_db)):
    data = action.model_dump()
    if data.get("event_data") is not None:
        try:
            data["event_data"] = validate_event_data(
                action.action_type, data["event_data"])
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail={"event_data": e.errors()},
            ) from e
    db_action = Action(**data)
    db.add(db_action)
    try:
        db.commit()
        db.refresh(db_action)

        # If this action is linked to an initiative, update the initiative's complete field
        if db_action.linked_id:
            from app.models.initiative import Initiative

            total = (
                db.query(Action)
                .filter(Action.linked_id == db_action.linked_id)
                .with_entities(func.coalesce(func.sum(Action.amount), 0))
                .scalar()
            )
            initiative = db.query(Initiative).filter(
                Initiative.id == db_action.linked_id).first()
            if initiative:
                initiative.complete = int(total) if total is not None else 0
                db.commit()
                db.refresh(initiative)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create action or update initiative: {str(e)}"
        )

    return db_action


@router.get("/", response_model=list[ActionSchema])
def list_actions(db: Session = Depends(get_db), limit: int = None):
    query = db.query(Action).order_by(Action.date.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


_DIRECTORY_OF_GOOD_ACTION_TYPE = "Directory of Good Addition"


def _is_directory_of_good_action(action_type: str | None) -> bool:
    if not action_type:
        return False
    at = (action_type or "").strip()
    return at == _DIRECTORY_OF_GOOD_ACTION_TYPE or "directory of good" in at.lower()


@router.get("/recent", response_model=list[ActionSchema])
def get_latest_actions(
    db: Session = Depends(get_db), days: int = 30, action_type: ActionTypeValuesEnum = None
):
    """Recent actions. Featured DoG-linked actions first; then within each day, directory-of-good actions first, then by date desc."""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    featured_dog_ids = {
        str(row[0])
        for row in db.query(DirectoryOfGood.id).filter(
            DirectoryOfGood.featured.is_(True)
        ).all()
    }

    query = db.query(Action).filter(Action.date >= cutoff_date)
    if action_type:
        query = query.filter(Action.action_type == action_type)
    actions = query.all()

    def sort_key(a):
        linked = str(a.linked_id) if a.linked_id else None
        is_featured_dog = linked in featured_dog_ids
        day_ordinal = (a.date.date() if a.date else datetime.now(
            UTC).date()).toordinal()
        is_dog = _is_directory_of_good_action(a.action_type)
        ts = a.date.timestamp() if a.date else 0
        return (not is_featured_dog, -day_ordinal, not is_dog, -ts)

    actions.sort(key=sort_key)
    return actions


@router.patch("/{action_id}/photos", response_model=ActionSchema)
def update_action_photos(
    action_id: UUID,
    payload: ActionPhotosUpdate,
    db: Session = Depends(get_db),
):
    """Update the photo URLs for an action."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.image_urls = payload.image_urls
    db.commit()
    db.refresh(action)
    return action


@router.get("/{action_id}", response_model=ActionSchema)
def get_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/by_linked/{linked_id}", response_model=list[ActionSchema])
def get_actions_by_linked(
    linked_id: UUID,
    db: Session = Depends(get_db),
    days: int | None = Query(
        None, ge=1, description="Only return actions from the last N days"),
):
    query = db.query(Action).filter(Action.linked_id == linked_id)
    if days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        query = query.filter(Action.date >= cutoff)
    actions = query.order_by(Action.date.desc()).all()
    return actions


@router.delete("/{action_id}", response_model=ActionSchema)
def delete_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    linked_id = action.linked_id
    db.delete(action)
    db.commit()

    # If this action was linked to an initiative, update the initiative's complete field
    if linked_id:
        from app.models.initiative import Initiative

        total = (
            db.query(Action)
            .filter(Action.linked_id == linked_id)
            .with_entities(func.coalesce(func.sum(Action.amount), 0))
            .scalar()
        )
        initiative = db.query(Initiative).filter(
            Initiative.id == linked_id).first()
        if initiative:
            initiative.complete = int(total) if total is not None else 0
            db.commit()
            db.refresh(initiative)

    return action
