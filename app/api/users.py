from collections import Counter, defaultdict
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


def _rollup_map_event_data(ed: dict | None) -> tuple[int, int, int, int, float, int, int, int]:
    """Per-action map submission tallies."""
    ed = ed or {}
    t = ed.get("type", "")
    cleanup = 1 if t in ("cleanup", "Cleanup") else 0
    trash = 1 if t in ("trashReport", "trash_report", "Trash Report") else 0
    small = int(ed.get("small_bags") or 0)
    large = int(ed.get("large_bags") or 0)
    pounds = float(ed.get("pounds") or 0)
    quantity = int(ed.get("quantity") or 1)
    tree = quantity if t in ("tree_planting", "Tree Planting") else 0
    wildflower = quantity if t in ("wildflower_planting", "Wildflower Planting") else 0
    return cleanup, trash, small, large, pounds, tree, wildflower, tree + wildflower


def _aggregate_map_submissions(actions: list[Action]) -> tuple[int, int, int, int, float, int, int, int]:
    cleanup_count = trash_count = small_bags = large_bags = 0
    total_pounds = 0.0
    tree_count = wildflower_count = total_plantings = 0
    for a in actions:
        c_add, t_add, s_add, lg_add, p_add, tree_add, wild_add, plant_add = _rollup_map_event_data(
            a.event_data
        )
        cleanup_count += c_add
        trash_count += t_add
        small_bags += s_add
        large_bags += lg_add
        total_pounds += p_add
        tree_count += tree_add
        wildflower_count += wild_add
        total_plantings += plant_add
    return (
        cleanup_count,
        trash_count,
        small_bags,
        large_bags,
        total_pounds,
        tree_count,
        wildflower_count,
        total_plantings,
    )


def _build_map_campaign_breakdown(
    db: Session, actions: list[Action]
) -> list[MapCampaignStatsSchema]:
    campaign_buckets: dict[str | None, list[Action]] = defaultdict(list)
    for a in actions:
        campaign_buckets[str(a.linked_id) if a.linked_id else None].append(a)

    campaign_ids = [cid for cid in campaign_buckets if cid is not None]
    campaigns_by_id: dict[str, MapCampaign] = {}
    if campaign_ids:
        for c in db.query(MapCampaign).filter(MapCampaign.id.in_(campaign_ids)).all():
            campaigns_by_id[str(c.id)] = c

    map_campaign_breakdown: list[MapCampaignStatsSchema] = []
    for cid, bucket in campaign_buckets.items():
        campaign = campaigns_by_id.get(cid) if cid else None
        c_cleanup = c_trash = c_small = c_large = 0
        c_pounds = 0.0
        c_tree = c_wildflower = c_total_plantings = 0
        for a in bucket:
            dc, dt, ds, dlg, dp, d_tree, d_wildflower, d_total_plantings = _rollup_map_event_data(
                a.event_data
            )
            c_cleanup += dc
            c_trash += dt
            c_small += ds
            c_large += dlg
            c_pounds += dp
            c_tree += d_tree
            c_wildflower += d_wildflower
            c_total_plantings += d_total_plantings
        map_campaign_breakdown.append(
            MapCampaignStatsSchema(
                campaign_id=campaign.id if campaign else None,
                campaign_name=campaign.title if campaign else "Unknown campaign",
                submission_count=len(bucket),
                cleanup_count=c_cleanup,
                trash_report_count=c_trash,
                total_bags=c_small + c_large,
                total_pounds=c_pounds,
                tree_planting_count=c_tree,
                wildflower_planting_count=c_wildflower,
                total_plantings=c_total_plantings,
            )
        )
    map_campaign_breakdown.sort(key=lambda x: x.submission_count, reverse=True)
    return map_campaign_breakdown


def _directory_org_connection_counts(
    db: Session, user_id: UUID, org: DirectoryOfGood
) -> tuple[int, int, int]:
    """Followers (incoming user follows), partnerships, initiative connections for a DoG org."""
    org_conns = (
        db.query(Connection)
        .filter(Connection.created_by == user_id, Connection.from_type == "directory_of_good")
        .all()
    )
    org_initiative_conns = sum(1 for c in org_conns if c.connection_type == "contribution")
    org_partnerships = sum(1 for c in org_conns if c.connection_type == "partnership")
    org_followers = (
        db.query(Connection)
        .filter(
            Connection.to_type == "directory_of_good",
            Connection.to_id == org.id,
            Connection.from_type == "user",
        )
        .count()
    )
    return org_followers, org_partnerships, org_initiative_conns


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

    actions = (
        db.query(Action)
        .filter(
            Action.user_id == user_id,
            Action.action_type == ActionTypeValuesEnum.map_submission.value,
        )
        .all()
    )
    (
        cleanup_count,
        trash_count,
        small_bags,
        large_bags,
        total_pounds,
        tree_count,
        wildflower_count,
        total_plantings,
    ) = _aggregate_map_submissions(actions)
    map_campaign_breakdown = _build_map_campaign_breakdown(db, actions)

    all_actions = db.query(Action).filter(Action.user_id == user_id).order_by(Action.date).all()
    first_date = all_actions[0].date if all_actions else None
    last_date = all_actions[-1].date if all_actions else None

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

    action_type_counts = dict(Counter(a.action_type for a in all_actions if a.action_type))

    user_conns = (
        db.query(Connection)
        .filter(Connection.created_by == user_id, Connection.from_type == "user")
        .all()
    )
    follows = sum(1 for c in user_conns if c.connection_type == "follow")
    contributions = sum(1 for c in user_conns if c.connection_type == "contribution")

    org = db.query(DirectoryOfGood).filter(DirectoryOfGood.user_id == user_id).first()
    org_id = org_name = None
    org_followers = org_partnerships = org_initiative_conns = 0
    if org:
        org_id = org.id
        org_name = org.name
        org_followers, org_partnerships, org_initiative_conns = _directory_org_connection_counts(
            db, user_id, org
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
        tree_planting_count=tree_count,
        wildflower_planting_count=wildflower_count,
        total_plantings=total_plantings,
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
