from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.schemas.action import ActionCreateSchema, ActionSchema
from app.schemas.action_types import ActionTypeValuesEnum

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


@router.get("/recent", response_model=list[ActionSchema])
def get_latest_action(
    db: Session = Depends(get_db), days: int = 7, action_type: ActionTypeValuesEnum = None
):
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    query = db.query(Action).filter(Action.date >= cutoff_date)
    if action_type:
        query = query.filter(Action.action_type == action_type)
    latest_actions = query.order_by(Action.date.desc()).all()
    if not latest_actions:
        raise HTTPException(
            status_code=404,
            detail=f"No actions found in the last {days} days with action_type '{action_type}'"
            if action_type
            else f"No actions found in the last {days} days",
        )
    return latest_actions


@router.get("/{action_id}", response_model=ActionSchema)
def get_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/by_linked/{linked_id}", response_model=list[ActionSchema])
def get_actions_by_linked(linked_id: UUID, db: Session = Depends(get_db)):
    actions = (
        db.query(Action).filter(Action.linked_id == linked_id).order_by(Action.date.desc()).all()
    )
    return actions


@router.delete("/{action_id}", response_model=ActionSchema)
def delete_action(action_id: UUID, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    db.delete(action)
    db.commit()
    return action
