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
from app.models.user import User as UserModel
from app.schemas.action import (
    ActionClaimCleanedSchema,
    ActionCreateSchema,
    ActionLikeBody,
    ActionPhotosUpdate,
    ActionSchema,
    ActionUpdateSchema,
    CleanupParticipationBody,
)
from app.schemas.action_types import ActionTypeValuesEnum
from app.schemas.event_data import EventDataType, validate_event_data
from app.schemas.map_campaign import MapCampaignTypeEnum

router = APIRouter(prefix="/actions", tags=["actions"])


def _require_active_user(
    db: Session,
    user_id: UUID,
    action_name: str = "perform this action",
) -> UserModel:
    """User-scoped action mutations require a registered active user row."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"User not found; sign in with a registered account to {action_name}",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail=f"Inactive users cannot {action_name}")
    return user


def _require_active_user_for_like(db: Session, user_id: UUID) -> UserModel:
    """Likes require a registered user row; anonymous or unknown ids are rejected."""
    return _require_active_user(db, user_id, "like actions")


def _like_uuids_from_action(a: Action) -> list[UUID]:
    """Parse [Action.like_user_ids] JSON: list of uuid strings, newest like first."""
    raw = a.like_user_ids
    if not raw:
        return []
    out: list[UUID] = []
    for item in raw:
        out.append(item if isinstance(item, UUID) else UUID(str(item).strip('"')))
    return out


def _set_like_user_ids(a: Action, uids: list[UUID]) -> None:
    a.like_user_ids = [str(u) for u in uids]


def _event_data_without_nulls(event_data: dict | None) -> dict | None:
    if event_data is None:
        return None
    return {key: value for key, value in event_data.items() if value is not None}


def _action_to_schema(a: Action, for_user_id: UUID | None) -> ActionSchema:
    uids = _like_uuids_from_action(a)
    n = len(uids)
    me = (for_user_id in uids) if for_user_id is not None else False
    return ActionSchema(
        id=a.id,
        action_type=a.action_type,
        amount=a.amount,
        date=a.date,
        image_urls=a.image_urls or [],
        linked_id=a.linked_id,
        user_id=a.user_id,
        latitude=a.latitude,
        longitude=a.longitude,
        event_data=_event_data_without_nulls(a.event_data),
        like_user_ids=uids,
        like_count=n,
        liked_by_me=me,
        is_active=a.is_active,
        resolved_at=a.resolved_at,
        resolved_by_user_id=a.resolved_by_user_id,
        resolved_by_action_id=a.resolved_by_action_id,
        source_trash_report_id=a.source_trash_report_id,
    )


def _actions_to_schemas(actions: list[Action], for_user_id: UUID | None) -> list[ActionSchema]:
    if not actions:
        return []
    return [_action_to_schema(a, for_user_id) for a in actions]


def _one_action_to_schema(a: Action, for_user_id: UUID | None) -> ActionSchema:
    return _action_to_schema(a, for_user_id)


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


def _should_create_initiative_mirror(db: Session, db_action: Action) -> bool:
    """Only mirror allowed map submission event types to linked initiatives."""
    if db_action.linked_id is None or db_action.event_data is None:
        return False

    campaign = db.query(MapCampaign).filter(MapCampaign.id == db_action.linked_id).first()
    if not campaign:
        return False

    event_type = db_action.event_data.get("type")
    if event_type is None:
        return False

    # Never mirror trash reports to initiatives.
    if event_type == EventDataType.trash_report.value:
        return False

    if campaign.map_campaign_type == MapCampaignTypeEnum.cleanup_map.value:
        return event_type in (
            EventDataType.cleanup.value,
            EventDataType.cleanup_route.value,
        )
    if campaign.map_campaign_type == MapCampaignTypeEnum.planting_map.value:
        return event_type in (
            EventDataType.tree_planting.value,
            EventDataType.wildflower_planting.value,
        )
    return False


def _initiative_amount_for_action(db: Session, db_action: Action) -> float | None:
    """Map campaign submissions can contribute campaign-specific units to initiatives."""
    if db_action.linked_id is None:
        return db_action.amount
    campaign = db.query(MapCampaign).filter(MapCampaign.id == db_action.linked_id).first()
    if not campaign or not db_action.event_data:
        return db_action.amount
    if (
        campaign.map_campaign_type == MapCampaignTypeEnum.cleanup_map.value
        or campaign.title == "Cleanup Map"
    ):
        small = db_action.event_data.get("small_bags")
        large = db_action.event_data.get("large_bags")
        total_bags = (small if small is not None else 0) + (large if large is not None else 0)
        return float(total_bags) if total_bags else 1.0
    if campaign.map_campaign_type == MapCampaignTypeEnum.planting_map.value:
        event_type = db_action.event_data.get("type")
        if event_type in (
            EventDataType.tree_planting.value,
            EventDataType.wildflower_planting.value,
        ):
            quantity = db_action.event_data.get("quantity")
            return float(quantity) if quantity else 1.0
    return db_action.amount


def _event_type(action: Action) -> str | None:
    if not action.event_data:
        return None
    return action.event_data.get("type")


def _is_cleanup(action: Action) -> bool:
    return _event_type(action) == EventDataType.cleanup.value


def _is_trash_report(action: Action) -> bool:
    return _event_type(action) == EventDataType.trash_report.value


def _require_cleanup_action(db: Session, action_id: UUID) -> Action:
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Cleanup not found")
    if action.action_type != ActionTypeValuesEnum.map_submission.value or not _is_cleanup(action):
        raise HTTPException(status_code=400, detail="Action is not a cleanup map submission")
    return action


def _user_ids_from_event_list(event_data: dict, field: str) -> list[UUID]:
    raw = event_data.get(field) or []
    return [item if isinstance(item, UUID) else UUID(str(item).strip('"')) for item in raw]


def _set_event_user_ids(action: Action, field: str, user_ids: list[UUID]) -> None:
    data = dict(action.event_data or {})
    data[field] = [str(user_id) for user_id in user_ids]
    action.event_data = validate_event_data(action.action_type, data)


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
            like_user_ids=[],
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
            .filter(Action.linked_id == iid, Action.is_active.is_(True))
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
        initiative_ids: list[UUID] = []
        if _should_create_initiative_mirror(db, db_action):
            initiative_ids = _initiative_ids_for_map_campaign(db, db_action.linked_id)
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
    return _one_action_to_schema(db_action, None)


@router.get("/", response_model=list[ActionSchema])
def list_actions(
    db: Session = Depends(get_db),
    limit: int = None,
    include_inactive: bool = Query(False, description="Include resolved/inactive actions."),
    for_user_id: UUID | None = Query(
        default=None, description="If set, each action includes whether this user liked it."
    ),
):
    query = db.query(Action).order_by(Action.date.desc())
    if not include_inactive:
        query = query.filter(Action.is_active.is_(True))
    if limit is not None:
        query = query.limit(limit)
    rows = query.all()
    return _actions_to_schemas(rows, for_user_id)


_DIRECTORY_OF_GOOD_ACTION_TYPE = "Directory of Good Addition"


def _is_directory_of_good_action(action_type: str | None) -> bool:
    if not action_type:
        return False
    at = (action_type or "").strip()
    return at == _DIRECTORY_OF_GOOD_ACTION_TYPE or "directory of good" in at.lower()


@router.get("/recent", response_model=list[ActionSchema])
def get_latest_actions(
    db: Session = Depends(get_db),
    days: int = 30,
    action_type: ActionTypeValuesEnum = None,
    include_inactive: bool = Query(False, description="Include resolved/inactive actions."),
    for_user_id: UUID | None = Query(
        default=None, description="If set, each action includes whether this user liked it."
    ),
):
    # Recent actions: featured Directory of Good-linked first; then per day,
    # directory-of-good first, then by date descending.
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    featured_dog_ids = {
        str(row[0])
        for row in db.query(DirectoryOfGood.id).filter(DirectoryOfGood.featured.is_(True)).all()
    }

    query = db.query(Action).filter(Action.date >= cutoff_date)
    if not include_inactive:
        query = query.filter(Action.is_active.is_(True))
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
    return _actions_to_schemas(actions, for_user_id)


@router.post("/{action_id}/like", response_model=ActionSchema)
def add_action_like(action_id: UUID, body: ActionLikeBody, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    _require_active_user_for_like(db, body.user_id)
    cur = _like_uuids_from_action(action)
    if body.user_id not in cur:
        _set_like_user_ids(action, [body.user_id] + [u for u in cur if u != body.user_id])
        try:
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to add like: {e!s}") from e
        db.refresh(action)
    return _one_action_to_schema(action, body.user_id)


@router.delete("/{action_id}/like", response_model=ActionSchema)
def remove_action_like(
    action_id: UUID,
    user_id: UUID = Query(..., description="Database id of the user unliking the action"),
    db: Session = Depends(get_db),
):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    _require_active_user_for_like(db, user_id)
    cur = _like_uuids_from_action(action)
    if user_id in cur:
        _set_like_user_ids(action, [u for u in cur if u != user_id])
        try:
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to remove like: {e!s}") from e
        db.refresh(action)
    return _one_action_to_schema(action, user_id)


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
    return _one_action_to_schema(action, None)


def _require_editable_cleanup(action: Action, user_id: UUID) -> None:
    if not action.is_active:
        raise HTTPException(status_code=400, detail="Resolved actions cannot be edited")
    if action.user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the submission owner can edit it")
    if action.action_type != ActionTypeValuesEnum.map_submission.value or not _is_cleanup(action):
        raise HTTPException(status_code=400, detail="Only cleanup map submissions can be edited")


def _apply_action_update(action: Action, payload: ActionUpdateSchema) -> None:
    if payload.event_data is not None:
        try:
            event_data = validate_event_data(action.action_type, payload.event_data)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail={"event_data": e.errors()}) from e
        if event_data and event_data.get("type") != EventDataType.cleanup.value:
            raise HTTPException(status_code=400, detail="Cleanup edits must keep type Cleanup")
        action.event_data = event_data
    updates = {
        "amount": payload.amount,
        "image_urls": payload.image_urls,
        "date": payload.date,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
    }
    for field, value in updates.items():
        if value is not None:
            setattr(action, field, value)


@router.patch("/{action_id}", response_model=ActionSchema)
def update_action(
    action_id: UUID,
    payload: ActionUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update a cleanup map submission owned by the requesting user."""
    _require_active_user(db, payload.user_id, "edit cleanup submissions")
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    _require_editable_cleanup(action, payload.user_id)
    _apply_action_update(action, payload)

    try:
        db.commit()
        db.refresh(action)
        if action.linked_id is not None:
            _update_initiative_completes(db, [], action.linked_id)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update action: {e!s}") from e
    return _one_action_to_schema(action, payload.user_id)


@router.post("/{trash_report_id}/claim-cleaned", response_model=ActionSchema)
def claim_trash_report_cleaned(
    trash_report_id: UUID,
    payload: ActionClaimCleanedSchema,
    db: Session = Depends(get_db),
):
    """Create a cleanup from an active trash report and resolve the original report."""
    if payload.user_id is not None:
        _require_active_user(db, payload.user_id, "claim trash reports")
    trash_report = db.query(Action).filter(Action.id == trash_report_id).first()
    if not trash_report:
        raise HTTPException(status_code=404, detail="Trash report not found")
    if trash_report.resolved_at is not None or not trash_report.is_active:
        raise HTTPException(status_code=400, detail="Trash report has already been resolved")
    if (
        trash_report.action_type != ActionTypeValuesEnum.map_submission.value
        or not _is_trash_report(trash_report)
    ):
        raise HTTPException(
            status_code=400,
            detail="Only trash report map submissions can be claimed",
        )

    try:
        event_data = validate_event_data(
            ActionTypeValuesEnum.map_submission.value,
            payload.event_data,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail={"event_data": e.errors()}) from e
    if not event_data or event_data.get("type") != EventDataType.cleanup.value:
        raise HTTPException(status_code=400, detail="Claim payload must create a Cleanup")

    cleanup = Action(
        action_type=ActionTypeValuesEnum.map_submission.value,
        amount=payload.amount,
        date=payload.date or datetime.now(UTC),
        image_urls=payload.image_urls or [],
        linked_id=trash_report.linked_id,
        user_id=payload.user_id,
        latitude=payload.latitude if payload.latitude is not None else trash_report.latitude,
        longitude=payload.longitude if payload.longitude is not None else trash_report.longitude,
        event_data=event_data,
        like_user_ids=[],
        source_trash_report_id=trash_report.id,
    )
    db.add(cleanup)
    try:
        db.flush()
        # Keep is_active so the trash report stays in feeds; resolved_at hides it from the map.
        trash_report.resolved_at = datetime.now(UTC)
        trash_report.resolved_by_user_id = payload.user_id
        trash_report.resolved_by_action_id = cleanup.id
        initiative_ids = (
            _initiative_ids_for_map_campaign(db, cleanup.linked_id)
            if cleanup.linked_id is not None
            else []
        )
        initiative_amount = _initiative_amount_for_action(db, cleanup)
        _create_mirror_actions(db, cleanup, initiative_ids, initiative_amount)
        db.commit()
        db.refresh(cleanup)
        _update_initiative_completes(db, initiative_ids, cleanup.linked_id)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to claim trash report: {e!s}") from e
    return _one_action_to_schema(cleanup, payload.user_id)


@router.get("/{cleanup_id}/rsvps", response_model=list[UUID])
def list_cleanup_rsvps(cleanup_id: UUID, db: Session = Depends(get_db)):
    action = _require_cleanup_action(db, cleanup_id)
    return _user_ids_from_event_list(action.event_data or {}, "rsvp_user_ids")


@router.post("/{cleanup_id}/rsvp", response_model=ActionSchema)
def upsert_cleanup_rsvp(
    cleanup_id: UUID,
    payload: CleanupParticipationBody,
    db: Session = Depends(get_db),
):
    action = _require_cleanup_action(db, cleanup_id)
    _require_active_user(db, payload.user_id, "RSVP to cleanups")
    user_ids = _user_ids_from_event_list(action.event_data or {}, "rsvp_user_ids")
    if payload.user_id not in user_ids:
        _set_event_user_ids(action, "rsvp_user_ids", user_ids + [payload.user_id])
    try:
        db.commit()
        db.refresh(action)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save RSVP: {e!s}") from e
    return _one_action_to_schema(action, payload.user_id)


@router.delete("/{cleanup_id}/rsvp", response_model=ActionSchema)
def delete_cleanup_rsvp(
    cleanup_id: UUID,
    user_id: UUID = Query(..., description="Database id of the user removing their RSVP"),
    db: Session = Depends(get_db),
):
    action = _require_cleanup_action(db, cleanup_id)
    _require_active_user(db, user_id, "remove cleanup RSVPs")
    user_ids = _user_ids_from_event_list(action.event_data or {}, "rsvp_user_ids")
    _set_event_user_ids(action, "rsvp_user_ids", [uid for uid in user_ids if uid != user_id])
    try:
        db.commit()
        db.refresh(action)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove RSVP: {e!s}") from e
    return _one_action_to_schema(action, user_id)


@router.get("/{cleanup_id}/attendance", response_model=list[UUID])
def list_cleanup_attendance(cleanup_id: UUID, db: Session = Depends(get_db)):
    action = _require_cleanup_action(db, cleanup_id)
    return _user_ids_from_event_list(action.event_data or {}, "attended_user_ids")


@router.post("/{cleanup_id}/attendance", response_model=ActionSchema)
def mark_cleanup_attendance(
    cleanup_id: UUID,
    payload: CleanupParticipationBody,
    db: Session = Depends(get_db),
):
    action = _require_cleanup_action(db, cleanup_id)
    _require_active_user(db, payload.user_id, "mark cleanup attendance")
    user_ids = _user_ids_from_event_list(action.event_data or {}, "attended_user_ids")
    if payload.user_id not in user_ids:
        _set_event_user_ids(action, "attended_user_ids", user_ids + [payload.user_id])
    try:
        db.commit()
        db.refresh(action)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to mark attendance: {e!s}") from e
    return _one_action_to_schema(action, payload.user_id)


@router.get("/{action_id}", response_model=ActionSchema)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    for_user_id: UUID | None = Query(
        default=None, description="If set, includes whether this user liked the action."
    ),
):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return _one_action_to_schema(action, for_user_id)


@router.get("/by_linked/{linked_id}", response_model=list[ActionSchema])
def get_actions_by_linked(
    linked_id: UUID,
    db: Session = Depends(get_db),
    days: int | None = Query(None, ge=1, description="Only return actions from the last N days"),
    include_inactive: bool = Query(False, description="Include resolved/inactive actions."),
    for_user_id: UUID | None = Query(
        default=None, description="If set, each action includes whether this user liked it."
    ),
):
    query = db.query(Action).filter(Action.linked_id == linked_id)
    if not include_inactive:
        query = query.filter(Action.is_active.is_(True))
    if days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        query = query.filter(Action.date >= cutoff)
    actions = query.order_by(Action.date.desc()).all()
    return _actions_to_schemas(actions, for_user_id)


@router.get("/user/{user_id}", response_model=list[ActionSchema])
def get_actions_by_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, description="Maximum number of actions to return"),
    action_type: ActionTypeValuesEnum | None = Query(None),
    include_inactive: bool = Query(False, description="Include resolved/inactive actions."),
):
    """All actions submitted by a specific user, newest first."""
    query = db.query(Action).filter(Action.user_id == user_id).order_by(Action.date.desc())
    if not include_inactive:
        query = query.filter(Action.is_active.is_(True))
    if action_type:
        query = query.filter(Action.action_type == action_type)
    if limit:
        query = query.limit(limit)
    return _actions_to_schemas(query.all(), user_id)


@router.delete("/{action_id}", response_model=ActionSchema)
def delete_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    response_schema = _one_action_to_schema(action, None)
    linked_id = action.linked_id
    db.delete(action)
    db.commit()

    # If this action was linked to an initiative, update the initiative's complete field
    if linked_id:
        from app.models.initiative import Initiative

        total = (
            db.query(Action)
            .filter(Action.linked_id == linked_id, Action.is_active.is_(True))
            .with_entities(func.coalesce(func.sum(Action.amount), 0))
            .scalar()
        )
        initiative = db.query(Initiative).filter(Initiative.id == linked_id).first()
        if initiative:
            initiative.complete = int(total) if total is not None else 0
            db.commit()
            db.refresh(initiative)

    return response_schema
