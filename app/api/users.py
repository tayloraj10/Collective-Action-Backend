from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    Validates required fields and checks for duplicate emails.
    """
    if not user.email:
        raise HTTPException(
            status_code=422, detail="Email is required")
    existing = db.query(UserModel).filter(
        UserModel.email == user.email).first()
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
    user = db.query(UserModel).filter(
        UserModel.firebase_user_id == firebase_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/db/{user_id}", response_model=UserSchema)
def get_user_by_user_id(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a user by their unique ID.
    Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(
        UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user_update: UserCreate, db: Session = Depends(get_db)):
    """
    Update an existing user's information.
    Checks for email uniqueness and applies partial updates.
    Raises 404 if the user is not found.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email already exists for another user
    if user_update.email and user_update.email != user.email:
        existing = db.query(UserModel).filter(
            UserModel.email == user_update.email).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Email already registered")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "id":
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


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
