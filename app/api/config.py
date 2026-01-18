from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.models.status import Status
from app.models.action_types import ActionTypes
from app.schemas.category import CategorySchema, CategoryCreate
from app.schemas.status import StatusSchema, StatusCreate
from app.schemas.action_types import ActionTypeSchema, ActionTypeCreate

categories_router = APIRouter(prefix="/categories", tags=["categories"])
statuses_router = APIRouter(prefix="/statuses", tags=["statuses"])
action_types_router = APIRouter(prefix="/action_types", tags=["action_types"])


# Category Endpoints
@categories_router.post("/", response_model=CategorySchema)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@categories_router.get("/", response_model=list[CategorySchema])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@categories_router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@categories_router.put("/{category_id}", response_model=CategorySchema)
def update_category(category_id: str, category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(Category).get(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db_category.name = category.name
    db.commit()
    db.refresh(db_category)
    return db_category


@categories_router.delete("/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    db_category = db.query(Category).get(category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted"}


# Status Endpoints
@statuses_router.post("/", response_model=StatusSchema)
def create_status(status: StatusCreate, db: Session = Depends(get_db)):
    db_status = Status(name=status.name, status_type=status.status_type)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status


@statuses_router.get("/", response_model=list[StatusSchema])
def list_statuses(db: Session = Depends(get_db)):
    return db.query(Status).all()


@statuses_router.get("/{status_id}", response_model=StatusSchema)
def get_status(status_id: str, db: Session = Depends(get_db)):
    status = db.query(Status).get(status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status


@statuses_router.get("/by_type/{status_type}", response_model=list[StatusSchema])
def get_statuses_by_type(status_type: str, db: Session = Depends(get_db)):
    statuses = db.query(Status).filter(Status.status_type == status_type).all()
    if not statuses:
        raise HTTPException(
            status_code=404, detail="No statuses found for this type")
    return statuses


@statuses_router.put("/{status_id}", response_model=StatusSchema)
def update_status(status_id: str, status: StatusCreate, db: Session = Depends(get_db)):
    db_status = db.query(Status).get(status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")
    db_status.name = status.name
    db_status.status_type = status.status_type
    db.commit()
    db.refresh(db_status)
    return db_status


@statuses_router.delete("/{status_id}")
def delete_status(status_id: str, db: Session = Depends(get_db)):
    db_status = db.query(Status).get(status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")
    db.delete(db_status)
    db.commit()
    return {"detail": "Status deleted"}


# ActionTypes Endpoints
@action_types_router.post("/", response_model=ActionTypeSchema)
def create_action_type(action_type: ActionTypeCreate, db: Session = Depends(get_db)):
    db_action_type = ActionTypes(name=action_type.name)
    db.add(db_action_type)
    db.commit()
    db.refresh(db_action_type)
    return db_action_type


@action_types_router.get("/", response_model=list[ActionTypeSchema])
def list_action_types(db: Session = Depends(get_db)):
    return db.query(ActionTypes).all()


@action_types_router.get("/{action_type_id}", response_model=ActionTypeSchema)
def get_action_type(action_type_id: str, db: Session = Depends(get_db)):
    action_type = db.query(ActionTypes).get(action_type_id)
    if not action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    return action_type


@action_types_router.put("/{action_type_id}", response_model=ActionTypeSchema)
def update_action_type(action_type_id: str, action_type: ActionTypeCreate, db: Session = Depends(get_db)):
    db_action_type = db.query(ActionTypes).get(action_type_id)
    if not db_action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    db_action_type.name = action_type.name
    db.commit()
    db.refresh(db_action_type)
    return db_action_type


@action_types_router.delete("/{action_type_id}")
def delete_action_type(action_type_id: str, db: Session = Depends(get_db)):
    db_action_type = db.query(ActionTypes).get(action_type_id)
    if not db_action_type:
        raise HTTPException(status_code=404, detail="ActionType not found")
    db.delete(db_action_type)
    db.commit()
    return {"detail": "ActionType deleted"}
