from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.initiative import Initiative
from app.models.status import Status
from app.schemas.initiative import InitiativeSchema, InitiativeCreateSchema
from uuid import UUID

from app.schemas.status import StatusTypeEnum, StatusValuesEnum

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


@router.post("/", response_model=InitiativeSchema)
def create_initiative(initiative: InitiativeCreateSchema, db: Session = Depends(get_db)):
    db_initiative = Initiative(**initiative.dict())
    db.add(db_initiative)
    db.commit()
    db.refresh(db_initiative)
    return db_initiative


@router.get("/", response_model=list[InitiativeSchema])
def list_initiatives(db: Session = Depends(get_db)):
    return db.query(Initiative).all()


@router.get("/active", response_model=list[InitiativeSchema])
def list_active_initiatives(db: Session = Depends(get_db)):
    active_status = db.query(Status).filter(
        Status.name == StatusValuesEnum.active and Status.status_type == StatusTypeEnum.status).first()
    if not active_status:
        return []
    return db.query(Initiative).filter(Initiative.status_id == active_status.id).all()


@router.get("/summary", response_model=list[InitiativeSchema])
def list_initiatives_summary(db: Session = Depends(get_db)):
    return db.query(Initiative).all()


@router.get("/{initiative_id}", response_model=InitiativeSchema)
def get_initiative(initiative_id: UUID, db: Session = Depends(get_db)):
    initiative = db.query(Initiative).filter(
        Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return initiative
