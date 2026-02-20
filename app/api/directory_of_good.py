from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.directory_of_good import DirectoryOfGood
from app.schemas.directory_of_good import (
    DirectoryOfGoodCreate,
    DirectoryOfGoodSchema,
    DirectoryOfGoodUpdate,
)

router = APIRouter(prefix="/directory-of-good", tags=["directory-of-good"])


ACTION_TYPE_DIRECTORY_OF_GOOD_ADDITION = "Directory of Good Addition"


@router.post("/", response_model=DirectoryOfGoodSchema, status_code=status.HTTP_201_CREATED)
def create_entry(body: DirectoryOfGoodCreate, db: Session = Depends(get_db)):
    """Create a new directory of good entry and an action record."""
    data = body.model_dump()
    entry = DirectoryOfGood(**data)
    db.add(entry)
    db.flush()  # get entry.id before commit
    action = Action(
        action_type=ACTION_TYPE_DIRECTORY_OF_GOOD_ADDITION,
        linked_id=entry.id,
    )
    db.add(action)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[DirectoryOfGoodSchema])
def list_entries(db: Session = Depends(get_db)):
    """List all directory of good entries."""
    return db.query(DirectoryOfGood).order_by(DirectoryOfGood.created_at.desc()).all()


@router.get("/{entry_id}", response_model=DirectoryOfGoodSchema)
def get_entry(entry_id: UUID, db: Session = Depends(get_db)):
    """Get a single directory of good entry by ID."""
    entry = db.query(DirectoryOfGood).filter(DirectoryOfGood.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Directory of good entry not found")
    return entry


@router.get("/by-user/{user_id}", response_model=list[DirectoryOfGoodSchema])
def list_entries_by_user(user_id: UUID, db: Session = Depends(get_db)):
    """List directory entries linked to a specific user."""
    return db.query(DirectoryOfGood).filter(DirectoryOfGood.user_id == user_id).all()


class FeatureUpdate(BaseModel):
    featured: bool


@router.patch("/{entry_id}/feature", response_model=DirectoryOfGoodSchema)
def set_featured(
    entry_id: UUID, body: FeatureUpdate, db: Session = Depends(get_db)
):
    """Feature or unfeature a directory of good entry."""
    entry = db.query(DirectoryOfGood).filter(DirectoryOfGood.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Directory of good entry not found")
    entry.featured = body.featured
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=DirectoryOfGoodSchema)
def update_entry(
    entry_id: UUID, body: DirectoryOfGoodUpdate, db: Session = Depends(get_db)
):
    """Update a directory of good entry (partial update)."""
    entry = db.query(DirectoryOfGood).filter(DirectoryOfGood.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Directory of good entry not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: UUID, db: Session = Depends(get_db)):
    """Delete a directory of good entry."""
    entry = db.query(DirectoryOfGood).filter(DirectoryOfGood.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Directory of good entry not found")
    db.delete(entry)
    db.commit()
    return None
