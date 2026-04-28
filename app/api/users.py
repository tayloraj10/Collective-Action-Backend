from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.connection import Connection
from app.models.directory_of_good import DirectoryOfGood
from app.models.map_campaign import MapCampaign
from app.models.user import User as UserModel
from app.schemas.action_types import ActionTypeValuesEnum
from app.schemas.user import (
    MapCampaignStatsSchema,
    UserCreate,
    UserPhotoUpdate,
    UserSchema,
    UserStatsSchema,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    Validates required fields and checks for duplicate emails.
    """
    if not user.email:
        raise HTTPException(status_code=422, detail="Email is required")
    existing = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = UserModel(
        email=user.email,
        name=user.name,
        photo_url=user.photo_url,
        firebase_user_id=user.firebase_user_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserSchema])
def list_users(db: Session = Depends(get_db)):
    """
    Retrieve a list of all users from the database.
    """
    return db.query(UserModel).all()


@router.get("/{firebase_id}", response_model=UserSchema)
def get_user_by_firebase_id(firebase_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by their unique ID.
    Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(UserModel.firebase_user_id == firebase_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/db/{user_id}", response_model=UserSchema)
def get_user_by_user_id(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by their unique ID.
    Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update an existing user's information (partial update).
    Cannot update photo_url, firebase_user_id, or is_active; use dedicated endpoints for those.
    Checks for email uniqueness. Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email already exists for another user
    if user_update.email and user_update.email != user.email:
        existing = db.query(UserModel).filter(UserModel.email == user_update.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "id":
            setattr(user, field, value)

    user.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/photo", response_model=UserSchema)
def update_user_photo(user_id: UUID, payload: UserPhotoUpdate, db: Session = Depends(get_db)):
    """
    Update only a user's `photo_url`.

    Expected body:
      { "photo_url": "https://..." }
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.photo_url = payload.photo_url
    user.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(user)
    return user


@router.get("/db/{user_id}/stats", response_model=UserStatsSchema)
def get_user_stats(user_id: UUID, db: Session = Depends(get_db)):
    """Aggregated contribution and impact stats for a user."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ── Map impact ─────────────────────────────────────────────────────────
    actions = (
        db.query(Action)
        .filter(
            Action.user_id == user_id,
            Action.action_type == ActionTypeValuesEnum.map_submission.value,
        )
        .all()
    )
    cleanup_count = trash_count = small_bags = large_bags = 0
    total_pounds = 0.0
    for a in actions:
        ed = a.event_data or {}
        t = ed.get("type", "")
        if t == "cleanup":
            cleanup_count += 1
        elif t in ("trashReport", "trash_report"):
            trash_count += 1
        small_bags += int(ed.get("small_bags") or 0)
        large_bags += int(ed.get("large_bags") or 0)
        total_pounds += float(ed.get("pounds") or 0)

    # ── Per-campaign map breakdown ─────────────────────────────────────────
    from collections import defaultdict
    campaign_buckets: dict[str | None, list[Action]] = defaultdict(list)
    for a in actions:
        campaign_buckets[str(a.linked_id) if a.linked_id else None].append(a)

    # Pre-fetch all relevant campaign names in one query.
    campaign_ids = [
        cid for cid in campaign_buckets if cid is not None
    ]
    campaigns_by_id: dict[str, MapCampaign] = {}
    if campaign_ids:
        for c in db.query(MapCampaign).filter(MapCampaign.id.in_(campaign_ids)).all():
            campaigns_by_id[str(c.id)] = c

    map_campaign_breakdown: list[MapCampaignStatsSchema] = []
    for cid, bucket in campaign_buckets.items():
        campaign = campaigns_by_id.get(cid) if cid else None
        c_cleanup = c_trash = c_small = c_large = 0
        c_pounds = 0.0
        for a in bucket:
            ed = a.event_data or {}
            t = ed.get("type", "")
            if t == "cleanup":
                c_cleanup += 1
            elif t in ("trashReport", "trash_report"):
                c_trash += 1
            c_small += int(ed.get("small_bags") or 0)
            c_large += int(ed.get("large_bags") or 0)
            c_pounds += float(ed.get("pounds") or 0)
        map_campaign_breakdown.append(
            MapCampaignStatsSchema(
                campaign_id=campaign.id if campaign else None,
                campaign_name=campaign.title if campaign else "Unknown campaign",
                submission_count=len(bucket),
                cleanup_count=c_cleanup,
                trash_report_count=c_trash,
                total_bags=c_small + c_large,
                total_pounds=c_pounds,
            )
        )
    # Sort by submission count descending.
    map_campaign_breakdown.sort(key=lambda x: x.submission_count, reverse=True)

    # ── All actions (for timeline) ─────────────────────────────────────────
    all_actions = (
        db.query(Action)
        .filter(Action.user_id == user_id)
        .order_by(Action.date)
        .all()
    )
    first_date = all_actions[0].date if all_actions else None
    last_date = all_actions[-1].date if all_actions else None

    # ── Initiative contribution actions ───────────────────────────────────
    init_actions = (
        db.query(Action)
        .filter(
            Action.user_id == user_id,
            Action.action_type == ActionTypeValuesEnum.initative.value,
        )
        .all()
    )
    initiative_action_count = len(init_actions)
    initiatives_participated = len(
        {str(a.linked_id) for a in init_actions if a.linked_id is not None}
    )

    # ── Action counts by type ──────────────────────────────────────────────
    from collections import Counter
    action_type_counts = dict(
        Counter(a.action_type for a in all_actions if a.action_type)
    )

    # ── Outgoing connections ───────────────────────────────────────────────
    user_conns = (
        db.query(Connection)
        .filter(Connection.created_by == user_id, Connection.from_type == "user")
        .all()
    )
    follows = sum(1 for c in user_conns if c.connection_type == "follow")
    contributions = sum(1 for c in user_conns if c.connection_type == "contribution")

    # ── Org stats (if user owns a DoG entry) ──────────────────────────────
    org = db.query(DirectoryOfGood).filter(DirectoryOfGood.user_id == user_id).first()
    org_id = org_name = None
    org_followers = org_partnerships = org_initiative_conns = 0
    if org:
        org_id = org.id
        org_name = org.name
        org_conns = (
            db.query(Connection)
            .filter(Connection.created_by == user_id, Connection.from_type == "directory_of_good")
            .all()
        )
        org_initiative_conns = sum(1 for c in org_conns if c.connection_type == "contribution")
        org_partnerships = sum(1 for c in org_conns if c.connection_type == "partnership")
        # Followers = connections where someone connected TO this org
        org_followers = (
            db.query(Connection)
            .filter(
                Connection.to_type == "directory_of_good",
                Connection.to_id == org.id,
                Connection.from_type == "user",
            )
            .count()
        )

    return UserStatsSchema(
        user_id=user_id,
        map_submission_count=len(actions),
        cleanup_count=cleanup_count,
        trash_report_count=trash_count,
        total_small_bags=small_bags,
        total_large_bags=large_bags,
        total_bags=small_bags + large_bags,
        total_pounds=total_pounds,
        initiative_action_count=initiative_action_count,
        initiatives_participated=initiatives_participated,
        map_campaign_breakdown=map_campaign_breakdown,
        action_type_counts=action_type_counts,
        follows_count=follows,
        contributions_count=contributions,
        org_id=org_id,
        org_name=org_name,
        org_followers_count=org_followers,
        org_partnerships_count=org_partnerships,
        org_initiative_connections=org_initiative_conns,
        total_actions=len(all_actions),
        first_action_date=first_date,
        last_action_date=last_date,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a user by their unique ID.
    Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None
