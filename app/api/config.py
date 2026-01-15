from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.models.status import Status
from app.models.action_types import ActionTypes
from app.schemas.category import CategorySchema, CategoryCreate
from app.schemas.status import StatusSchema, StatusCreate
from app.schemas.action_types import ActionTypeSchema, ActionTypeCreate

router = APIRouter(prefix="/config", tags=["config"])

# Category Endpoints


@router.post("/categories", response_model=CategorySchema)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/categories", response_model=list[CategorySchema])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@router.get("/categories/{category_id}", response_model=CategorySchema)
def get_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=CategorySchema)
def update_category(category_id: str, category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(Category).get(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db_category.name = category.name
    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/categories/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    db_category = db.query(Category).get(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted"}

# Status Endpoints


@router.post("/statuses", response_model=StatusSchema)
def create_status(status: StatusCreate, db: Session = Depends(get_db)):
    db_status = Status(name=status.name)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status


@router.get("/statuses", response_model=list[StatusSchema])
def list_statuses(db: Session = Depends(get_db)):
    return db.query(Status).all()


@router.get("/statuses/{status_id}", response_model=StatusSchema)
def get_status(status_id: str, db: Session = Depends(get_db)):
    status = db.query(Status).get(status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status


@router.put("/statuses/{status_id}", response_model=StatusSchema)
def update_status(status_id: str, status: StatusCreate, db: Session = Depends(get_db)):
    db_status = db.query(Status).get(status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")
    db_status.name = status.name
    db.commit()
    db.refresh(db_status)
    return db_status


@router.delete("/statuses/{status_id}")
def delete_status(status_id: str, db: Session = Depends(get_db)):
    db_status = db.query(Status).get(status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")
    db.delete(db_status)
    db.commit()
    return {"detail": "Status deleted"}

# ActionTypes Endpoints


@router.post("/action_types", response_model=ActionTypeSchema)
def create_action_type(action_type: ActionTypeCreate, db: Session = Depends(get_db)):
    db_action_type = ActionTypes(name=action_type.name)
    db.add(db_action_type)
    db.commit()
    db.refresh(db_action_type)
    return db_action_type


@router.get("/action_types", response_model=list[ActionTypeSchema])
def list_action_types(db: Session = Depends(get_db)):
    return db.query(ActionTypes).all()


@router.get("/action_types/{action_type_id}", response_model=ActionTypeSchema)
def get_action_type(action_type_id: str, db: Session = Depends(get_db)):
    action_type = db.query(ActionTypes).get(action_type_id)
    if not action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    return action_type


@router.put("/action_types/{action_type_id}", response_model=ActionTypeSchema)
def update_action_type(action_type_id: str, action_type: ActionTypeCreate, db: Session = Depends(get_db)):
    db_action_type = db.query(ActionTypes).get(action_type_id)
    if not db_action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    db_action_type.name = action_type.name
    db.commit()
    db.refresh(db_action_type)
    return db_action_type


@router.delete("/action_types/{action_type_id}")
def delete_action_type(action_type_id: str, db: Session = Depends(get_db)):
    db_action_type = db.query(ActionTypes).get(action_type_id)
    if not db_action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    db.delete(db_action_type)
    db.commit()
    return {"detail": "ActionType deleted"}
