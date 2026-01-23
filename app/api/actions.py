from datetime import UTC, datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.action import Action
from app.schemas.action import ActionCreateSchema, ActionSchema
from app.schemas.action_types import ActionTypeValuesEnum

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/", response_model=ActionSchema)
def create_action(action: ActionCreateSchema, db: Session = Depends(get_db)):
    db_action = Action(**action.model_dump())
    db.add(db_action)
    try:
        db.commit()
        db.refresh(db_action)

        # If this action is linked to an initiative, update the initiative's complete field
        if db_action.linked_id:
            from app.models.initiative import Initiative
            total = db.query(Action).filter(Action.linked_id == db_action.linked_id).with_entities(
                func.coalesce(func.sum(Action.amount), 0)).scalar()
            initiative = db.query(Initiative).filter(
                Initiative.id == db_action.linked_id).first()
            if initiative:
                initiative.complete = int(total) if total is not None else 0
                db.commit()
                db.refresh(initiative)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create action or update initiative: {str(e)}")

    return db_action


@router.get("/", response_model=list[ActionSchema])
def list_actions(db: Session = Depends(get_db), limit: int = None):
    query = db.query(Action).order_by(Action.date.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@router.get("/recent", response_model=list[ActionSchema])
def get_latest_actions(
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
        db.query(Action).filter(Action.linked_id ==
                                linked_id).order_by(Action.date.desc()).all()
    )
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
        total = db.query(Action).filter(Action.linked_id == linked_id).with_entities(
            db.func.coalesce(db.func.sum(Action.amount), 0)).scalar()
        initiative = db.query(Initiative).filter(
            Initiative.id == linked_id).first()
        if initiative:
            initiative.complete = int(total) if total is not None else 0
            db.commit()
            db.refresh(initiative)

    return action
