from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.initiative import Initiative
from app.schemas.initiative import InitiativeSchema, InitiativeCreateSchema
from uuid import UUID

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
    return db.query(Initiative).filter(Initiative.is_active == True).all()


@router.get("/{initiative_id}", response_model=InitiativeSchema)
def get_initiative(initiative_id: UUID, db: Session = Depends(get_db)):
    initiative = db.query(Initiative).filter(
        Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return initiative
