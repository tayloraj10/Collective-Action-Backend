from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.action import Action
from app.schemas.action import ActionSchema, ActionCreateSchema
from uuid import UUID

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/", response_model=ActionSchema)
def create_action(action: ActionCreateSchema, db: Session = Depends(get_db)):
    db_action = Action(**action.dict())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


@router.get("/", response_model=list[ActionSchema])
def list_actions(db: Session = Depends(get_db), limit: int = None):
    query = db.query(Action).order_by(Action.date.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@router.get("/{action_id}", response_model=ActionSchema)
def get_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/by_initiative/{initiative_id}", response_model=list[ActionSchema])
def get_actions_by_initiative(initiative_id: UUID, db: Session = Depends(get_db)):
    actions = db.query(Action).filter(Action.initiative_id ==
                                      initiative_id).order_by(Action.created_at.desc()).all()
    return actions
