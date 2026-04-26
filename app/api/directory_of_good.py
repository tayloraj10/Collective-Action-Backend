from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.action import Action
from app.models.directory_of_good import DirectoryOfGood
from app.schemas.directory_of_good import (
    DirectoryOfGoodCreate,
    DirectoryOfGoodSchema,
    DirectoryOfGoodUpdate,
)
from app.services.directory_sheet_sync import SheetSyncResult, sync_interesting_people

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


class SheetSyncResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    rows_seen: int
    errors: list[str]


@router.post("/sync-from-google-sheet", response_model=SheetSyncResponse)
def sync_from_google_sheet(
    db: Session = Depends(get_db),
    x_sync_secret: str | None = Header(None, alias="X-Sync-Secret"),
):
    """Upsert directory rows from the configured 'Interesting People' Google Sheet.

    **Credentials:** If ``GOOGLE_APPLICATION_CREDENTIALS`` is set to a service account JSON
    path, that key is used. Otherwise **Application Default Credentials** are used (e.g. Cloud
    Run / GCE runtime service account). Enable the Google Sheets API for the project and share
    the spreadsheet with that service account email.

    When ``DIRECTORY_GOOGLE_SHEET_SYNC_SECRET`` is set, the same value must be sent in
    the ``X-Sync-Secret`` header.
    """
    secret = settings.DIRECTORY_GOOGLE_SHEET_SYNC_SECRET
    if secret and (not x_sync_secret or x_sync_secret != secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync secret")
    cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip() or None
    result: SheetSyncResult = sync_interesting_people(
        db,
        spreadsheet_id=settings.DIRECTORY_GOOGLE_SHEET_ID,
        sheet_gid=settings.DIRECTORY_GOOGLE_SHEET_GID,
        credentials_path=cred_path,
    )
    return SheetSyncResponse(
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        rows_seen=result.rows_seen,
        errors=result.errors,
    )


@router.get("/", response_model=list[DirectoryOfGoodSchema])
def list_entries(db: Session = Depends(get_db)):
    """List all directory of good entries."""
    return (
        db.query(DirectoryOfGood)
        .order_by(DirectoryOfGood.featured.desc(), DirectoryOfGood.created_at.desc())
        .all()
    )


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
def set_featured(entry_id: UUID, body: FeatureUpdate, db: Session = Depends(get_db)):
    """Feature or unfeature a directory of good entry."""
    entry = db.query(DirectoryOfGood).filter(DirectoryOfGood.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Directory of good entry not found")
    entry.featured = body.featured
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=DirectoryOfGoodSchema)
def update_entry(entry_id: UUID, body: DirectoryOfGoodUpdate, db: Session = Depends(get_db)):
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
