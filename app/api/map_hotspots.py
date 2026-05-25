from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.map_area_seeds import DEFAULT_AREA_SEEDS
from app.database import get_db
from app.models.area_captain import AreaCaptain
from app.models.map_area import MapArea
from app.models.map_campaign import MapCampaign
from app.models.map_hotspot import MapHotspot
from app.models.user import User
from app.schemas.area_captain import (
    AreaCaptainAssignSchema,
    AreaCaptainSchema,
)
from app.schemas.map_area import MapAreaCreateSchema, MapAreaSchema
from app.schemas.map_hotspot import (
    MapHotspotCreateSchema,
    MapHotspotSchema,
    MapHotspotUpdateSchema,
)
from app.utils.area_bounds import detect_area_for_point, point_in_bounds

router = APIRouter(prefix="/map-hotspots", tags=["map-hotspots"])


def _require_user(db: Session, user_id: UUID) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is not active")
    return user


def _require_campaign(db: Session, campaign_id: UUID) -> MapCampaign:
    campaign = db.query(MapCampaign).filter(MapCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Map campaign not found")
    return campaign


def _require_area(db: Session, area_id: UUID, campaign_id: UUID | None = None) -> MapArea:
    query = db.query(MapArea).filter(MapArea.id == area_id, MapArea.active.is_(True))
    if campaign_id is not None:
        query = query.filter(MapArea.map_campaign_id == campaign_id)
    area = query.first()
    if not area:
        raise HTTPException(status_code=404, detail="Map area not found")
    return area


def _seed_default_areas(db: Session, campaign_id: UUID) -> list[MapArea]:
    """Create default areas (NYC boroughs for now) when a campaign has none."""
    existing = (
        db.query(MapArea)
        .filter(MapArea.map_campaign_id == campaign_id, MapArea.active.is_(True))
        .count()
    )
    if existing:
        return _list_areas(db, campaign_id)

    created: list[MapArea] = []
    for seed in DEFAULT_AREA_SEEDS:
        bounds = seed["bounds"]
        area = MapArea(
            map_campaign_id=campaign_id,
            name=seed["name"],
            area_type=seed["area_type"].value,
            slug=seed["slug"],
            bounds=bounds.model_dump() if bounds else None,
            sort_order=seed.get("sort_order", 0),
        )
        db.add(area)
        db.flush()
        created.append(area)

    db.commit()
    return _list_areas(db, campaign_id)


def _list_areas(db: Session, campaign_id: UUID) -> list[MapArea]:
    return (
        db.query(MapArea)
        .filter(MapArea.map_campaign_id == campaign_id, MapArea.active.is_(True))
        .order_by(MapArea.sort_order, MapArea.name)
        .all()
    )


def _area_to_schema(area: MapArea) -> MapAreaSchema:
    return MapAreaSchema.model_validate(area)


def _captain_to_schema(db: Session, captain: AreaCaptain) -> AreaCaptainSchema:
    area = db.query(MapArea).filter(MapArea.id == captain.map_area_id).first()
    return AreaCaptainSchema(
        id=captain.id,
        map_area_id=captain.map_area_id,
        captain_user_id=captain.captain_user_id,
        assigned_by_user_id=captain.assigned_by_user_id,
        created_at=captain.created_at,
        updated_at=captain.updated_at,
        area=_area_to_schema(area) if area else None,
    )


def _hotspot_to_schema(db: Session, hotspot: MapHotspot) -> MapHotspotSchema:
    area = db.query(MapArea).filter(MapArea.id == hotspot.map_area_id).first()
    return MapHotspotSchema(
        id=hotspot.id,
        map_campaign_id=hotspot.map_campaign_id,
        map_area_id=hotspot.map_area_id,
        title=hotspot.title,
        description=hotspot.description,
        latitude=hotspot.latitude,
        longitude=hotspot.longitude,
        created_by=hotspot.created_by,
        active=hotspot.active,
        created_at=hotspot.created_at,
        updated_at=hotspot.updated_at,
        area=_area_to_schema(area) if area else None,
    )


def _list_captains_for_area(db: Session, area_id: UUID) -> list[AreaCaptain]:
    return db.query(AreaCaptain).filter(AreaCaptain.map_area_id == area_id).all()


def _list_captains_for_campaign(db: Session, campaign_id: UUID) -> list[AreaCaptain]:
    areas = _seed_default_areas(db, campaign_id)
    if not areas:
        return []
    area_ids = [a.id for a in areas]
    return (
        db.query(AreaCaptain)
        .filter(AreaCaptain.map_area_id.in_(area_ids))
        .order_by(AreaCaptain.created_at)
        .all()
    )


def _is_admin(user: User) -> bool:
    return bool(user.admin)


def _is_area_captain(db: Session, user_id: UUID, area_id: UUID) -> bool:
    return (
        db.query(AreaCaptain)
        .filter(AreaCaptain.map_area_id == area_id, AreaCaptain.captain_user_id == user_id)
        .first()
        is not None
    )


def _require_captain_or_admin(db: Session, user: User, area_id: UUID) -> MapArea:
    area = _require_area(db, area_id)
    if _is_admin(user):
        return area
    if not _is_area_captain(db, user.id, area_id):
        raise HTTPException(
            status_code=403,
            detail=f"Only a {area.name} captain or an admin can perform this action",
        )
    return area


@router.get("/campaign/{campaign_id}/areas", response_model=list[MapAreaSchema])
def list_areas(campaign_id: UUID, db: Session = Depends(get_db)):
    _require_campaign(db, campaign_id)
    areas = _seed_default_areas(db, campaign_id)
    return [_area_to_schema(a) for a in areas]


@router.post("/areas", response_model=MapAreaSchema)
def create_area(payload: MapAreaCreateSchema, db: Session = Depends(get_db)):
    _require_campaign(db, payload.map_campaign_id)
    acting = _require_user(db, payload.acting_user_id)
    if not _is_admin(acting):
        raise HTTPException(status_code=403, detail="Only admins can create map areas")

    if payload.parent_area_id:
        _require_area(db, payload.parent_area_id, payload.map_campaign_id)

    area = MapArea(
        map_campaign_id=payload.map_campaign_id,
        name=payload.name,
        area_type=payload.area_type.value,
        slug=payload.slug,
        parent_area_id=payload.parent_area_id,
        bounds=payload.bounds.model_dump() if payload.bounds else None,
        sort_order=payload.sort_order,
    )
    db.add(area)
    db.flush()
    db.commit()
    db.refresh(area)
    return _area_to_schema(area)


@router.get("/campaign/{campaign_id}/area-captains", response_model=list[AreaCaptainSchema])
def list_area_captains(campaign_id: UUID, db: Session = Depends(get_db)):
    _require_campaign(db, campaign_id)
    rows = _list_captains_for_campaign(db, campaign_id)
    return [_captain_to_schema(db, row) for row in rows]


@router.post("/area-captains/assign", response_model=AreaCaptainSchema)
def assign_area_captain(payload: AreaCaptainAssignSchema, db: Session = Depends(get_db)):
    area = _require_area(db, payload.map_area_id)
    acting = _require_user(db, payload.acting_user_id)
    _require_user(db, payload.captain_user_id)

    existing = (
        db.query(AreaCaptain)
        .filter(
            AreaCaptain.map_area_id == payload.map_area_id,
            AreaCaptain.captain_user_id == payload.captain_user_id,
        )
        .first()
    )
    if existing:
        return _captain_to_schema(db, existing)

    captain_count = (
        db.query(AreaCaptain).filter(AreaCaptain.map_area_id == payload.map_area_id).count()
    )

    if captain_count == 0:
        if not _is_admin(acting) and payload.captain_user_id != acting.id:
            raise HTTPException(
                status_code=403,
                detail="You can only claim captaincy for yourself on an unassigned area",
            )
    elif not _is_admin(acting) and not _is_area_captain(db, acting.id, payload.map_area_id):
        raise HTTPException(
            status_code=403,
            detail=f"Only existing {area.name} captains or an admin can add captains",
        )

    row = AreaCaptain(
        map_area_id=payload.map_area_id,
        captain_user_id=payload.captain_user_id,
        assigned_by_user_id=acting.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _captain_to_schema(db, row)


@router.delete("/area-captains/{assignment_id}", status_code=204)
def remove_area_captain(
    assignment_id: UUID,
    acting_user_id: UUID,
    db: Session = Depends(get_db),
):
    acting = _require_user(db, acting_user_id)
    row = db.query(AreaCaptain).filter(AreaCaptain.id == assignment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Captain assignment not found")

    area = _require_area(db, row.map_area_id)
    is_self = row.captain_user_id == acting.id
    if (
        not _is_admin(acting)
        and not is_self
        and not _is_area_captain(db, acting.id, row.map_area_id)
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Only {area.name} captains, the assigned user, or an admin can remove this captain"
            ),
        )

    db.delete(row)
    db.commit()
    return None


@router.get("/campaign/{campaign_id}", response_model=list[MapHotspotSchema])
def list_hotspots(
    campaign_id: UUID,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    _require_campaign(db, campaign_id)
    query = db.query(MapHotspot).filter(MapHotspot.map_campaign_id == campaign_id)
    if not include_inactive:
        query = query.filter(MapHotspot.active.is_(True))
    hotspots = query.order_by(MapHotspot.created_at.desc()).all()
    return [_hotspot_to_schema(db, h) for h in hotspots]


@router.post("/", response_model=MapHotspotSchema)
def create_hotspot(payload: MapHotspotCreateSchema, db: Session = Depends(get_db)):
    _require_campaign(db, payload.map_campaign_id)
    creator = _require_user(db, payload.created_by)
    area = _require_captain_or_admin(db, creator, payload.map_area_id)

    if area.map_campaign_id != payload.map_campaign_id:
        raise HTTPException(status_code=400, detail="Area does not belong to this campaign")

    areas = _list_areas(db, payload.map_campaign_id)
    detected = detect_area_for_point(payload.latitude, payload.longitude, areas)
    if detected is not None and detected.id != area.id:
        raise HTTPException(
            status_code=400,
            detail=f"Coordinates appear to be in {detected.name}, not {area.name}",
        )

    if area.bounds and not point_in_bounds(payload.latitude, payload.longitude, area.bounds):
        raise HTTPException(
            status_code=400,
            detail=f"Coordinates are outside the {area.name} area bounds",
        )

    existing = (
        db.query(MapHotspot)
        .filter(
            MapHotspot.map_area_id == payload.map_area_id,
            MapHotspot.active.is_(True),
        )
        .all()
    )
    for old in existing:
        old.active = False

    hotspot = MapHotspot(
        map_campaign_id=payload.map_campaign_id,
        map_area_id=payload.map_area_id,
        title=payload.title,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        created_by=payload.created_by,
    )
    db.add(hotspot)
    db.commit()
    db.refresh(hotspot)
    return _hotspot_to_schema(db, hotspot)


@router.patch("/{hotspot_id}", response_model=MapHotspotSchema)
def update_hotspot(
    hotspot_id: UUID,
    payload: MapHotspotUpdateSchema,
    db: Session = Depends(get_db),
):
    acting = _require_user(db, payload.acting_user_id)
    hotspot = db.query(MapHotspot).filter(MapHotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    _require_captain_or_admin(db, acting, hotspot.map_area_id)

    if payload.title is not None:
        hotspot.title = payload.title
    if payload.description is not None:
        hotspot.description = payload.description
    if payload.active is not None:
        hotspot.active = payload.active

    db.commit()
    db.refresh(hotspot)
    return _hotspot_to_schema(db, hotspot)


@router.delete("/{hotspot_id}", status_code=204)
def delete_hotspot(
    hotspot_id: UUID,
    acting_user_id: UUID,
    db: Session = Depends(get_db),
):
    acting = _require_user(db, acting_user_id)
    hotspot = db.query(MapHotspot).filter(MapHotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    _require_captain_or_admin(db, acting, hotspot.map_area_id)

    hotspot.active = False
    db.commit()
    return None
