from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.map_campaign import MapCampaign
from app.models.user import User
from app.schemas.map_campaign import (
    MapCampaignCreateSchema,
    MapCampaignSchema,
    MapCampaignTypeEnum,
)

router = APIRouter(prefix="/map-campaigns", tags=["map-campaigns"])


@router.post("/", response_model=MapCampaignSchema)
def create_map_campaign(
    campaign: MapCampaignCreateSchema, db: Session = Depends(get_db)
):
    creator = db.query(User).filter(User.id == campaign.created_by).first()
    if not creator:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {campaign.created_by} not found; cannot set created_by.",
        )
    data = campaign.model_dump()
    data["map_campaign_type"] = data["map_campaign_type"].value
    db_campaign = MapCampaign(**data)
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


@router.get("/", response_model=list[MapCampaignSchema])
def list_map_campaigns(db: Session = Depends(get_db)):
    return db.query(MapCampaign).all()


@router.get("/active", response_model=list[MapCampaignSchema])
def list_active_map_campaigns(db: Session = Depends(get_db)):
    return db.query(MapCampaign).filter(MapCampaign.active.is_(True)).all()


@router.get("/by-type/{campaign_type}", response_model=list[MapCampaignSchema])
def list_map_campaigns_by_type(
    campaign_type: MapCampaignTypeEnum,
    db: Session = Depends(get_db),
):
    return (
        db.query(MapCampaign)
        .filter(MapCampaign.map_campaign_type == campaign_type.value)
        .all()
    )


@router.get("/creator/{user_id}", response_model=list[MapCampaignSchema])
def list_map_campaigns_by_creator(user_id: UUID, db: Session = Depends(get_db)):
    return db.query(MapCampaign).filter(MapCampaign.created_by == user_id).all()


@router.get("/{campaign_id}", response_model=MapCampaignSchema)
def get_map_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = (
        db.query(MapCampaign).filter(MapCampaign.id == campaign_id).first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Map campaign not found")
    return campaign
