from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.directory_of_good import DirectoryOfGood
from app.models.link import Link
from app.models.map_campaign import MapCampaign
from app.schemas.action import ActionCreateSchema, ActionPhotosUpdate, ActionSchema
from app.schemas.action_types import ActionTypeValuesEnum
from app.schemas.event_data import validate_event_data

router = APIRouter(prefix="/actions", tags=["actions"])


def _initiative_ids_for_map_campaign(db: Session, map_campaign_id: UUID) -> list[UUID]:
    """Initiatives to mirror when a map submission is for this campaign."""
    links = (
        db.query(Link)
        .filter(
            Link.map_campaign_id == map_campaign_id,
            Link.initiative_id.isnot(None),
        )
        .all()
    )
    return list({link.initiative_id for link in links if link.initiative_id is not None})


def _initiative_amount_for_action(db: Session, db_action: Action) -> float | None:
    """Cleanup Map: small_bags + large_bags from event_data, else 1; else db_action.amount."""
    if db_action.linked_id is None:
        return db_action.amount
    campaign = db.query(MapCampaign).filter(MapCampaign.id == db_action.linked_id).first()
    if not campaign or campaign.title != "Cleanup Map" or not db_action.event_data:
        return db_action.amount
    small = db_action.event_data.get("small_bags")
    large = db_action.event_data.get("large_bags")
    total_bags = (small if small is not None else 0) + (large if large is not None else 0)
    return float(total_bags) if total_bags else 1.0


def _create_mirror_actions(
    db: Session,
    db_action: Action,
    initiative_ids: list[UUID],
    amount: float | None,
) -> None:
    for initiative_id in initiative_ids:
        initiative_action = Action(
            action_type=ActionTypeValuesEnum.initative.value,
            amount=amount,
            date=(db_action.date + timedelta(milliseconds=1)) if db_action.date else None,
            user_id=db_action.user_id,
            image_urls=db_action.image_urls,
            linked_id=initiative_id,
            latitude=db_action.latitude,
            longitude=db_action.longitude,
            event_data=db_action.event_data,
        )
        db.add(initiative_action)


def _update_initiative_completes(
    db: Session, initiative_ids: list[UUID], also_linked_id: UUID | None
) -> None:
    from app.models.initiative import Initiative

    to_update: set[UUID] = set(initiative_ids)
    if also_linked_id is not None:
        init = db.query(Initiative).filter(Initiative.id == also_linked_id).first()
        if init is not None:
            to_update.add(also_linked_id)
    for iid in to_update:
        total = (
            db.query(Action)
            .filter(Action.linked_id == iid)
            .with_entities(func.coalesce(func.sum(Action.amount), 0))
            .scalar()
        )
        initiative = db.query(Initiative).filter(Initiative.id == iid).first()
        if initiative:
            initiative.complete = int(total) if total is not None else 0
    if to_update:
        db.commit()
        for iid in to_update:
            initiative = db.query(Initiative).filter(Initiative.id == iid).first()
            if initiative:
                db.refresh(initiative)


@router.post("/", response_model=ActionSchema)
def create_action(action: ActionCreateSchema, db: Session = Depends(get_db)):
    data = action.model_dump()
    if data.get("event_data") is not None:
        try:
            data["event_data"] = validate_event_data(action.action_type, data["event_data"])
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail={"event_data": e.errors()},
            ) from e
    db_action = Action(**data)
    db.add(db_action)
    try:
        db.flush()
        initiative_ids = (
            _initiative_ids_for_map_campaign(db, db_action.linked_id)
            if db_action.linked_id is not None
            else []
        )
        initiative_amount = _initiative_amount_for_action(db, db_action)
        _create_mirror_actions(db, db_action, initiative_ids, initiative_amount)
        db.commit()
        db.refresh(db_action)
        _update_initiative_completes(db, initiative_ids, db_action.linked_id)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create action or update initiative: {str(e)}"
        ) from e
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
    # Recent actions: featured Directory of Good-linked first; then per day,
    # directory-of-good first, then by date descending.
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    featured_dog_ids = {
        str(row[0])
        for row in db.query(DirectoryOfGood.id).filter(DirectoryOfGood.featured.is_(True)).all()
    }

    query = db.query(Action).filter(Action.date >= cutoff_date)
    if action_type:
        query = query.filter(Action.action_type == action_type)
    actions = query.all()

    def sort_key(a):
        linked = str(a.linked_id) if a.linked_id else None
        is_featured_dog = linked in featured_dog_ids
        day_ordinal = (a.date.date() if a.date else datetime.now(UTC).date()).toordinal()
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
    days: int | None = Query(None, ge=1, description="Only return actions from the last N days"),
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
        initiative = db.query(Initiative).filter(Initiative.id == linked_id).first()
        if initiative:
            initiative.complete = int(total) if total is not None else 0
            db.commit()
            db.refresh(initiative)

    return action
