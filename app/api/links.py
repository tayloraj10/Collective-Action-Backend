from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.initiative import Initiative
from app.models.link import Link
from app.models.map_campaign import MapCampaign
from app.models.project import Project
from app.schemas.link import LinkCreateSchema, LinkSchema, LinkUpdateSchema

router = APIRouter(prefix="/links", tags=["links"])


def _validate_link_entities(link: LinkCreateSchema, db: Session) -> None:
    if link.project_id is not None:
        if db.query(Project).filter(Project.id == link.project_id).first() is None:
            raise HTTPException(status_code=404, detail="Project not found")
    if link.initiative_id is not None:
        if db.query(Initiative).filter(Initiative.id == link.initiative_id).first() is None:
            raise HTTPException(status_code=404, detail="Initiative not found")
    if link.map_campaign_id is not None:
        if db.query(MapCampaign).filter(MapCampaign.id == link.map_campaign_id).first() is None:
            raise HTTPException(
                status_code=404, detail="Map campaign not found")


def _raise_if_link_duplicate(link: LinkCreateSchema, db: Session) -> None:
    if link.project_id is not None and link.initiative_id is not None:
        if (
            db.query(Link)
            .filter(
                Link.project_id == link.project_id,
                Link.initiative_id == link.initiative_id,
            )
            .first()
            is not None
        ):
            raise HTTPException(status_code=400, detail="Link already exists")
    if link.project_id is not None and link.map_campaign_id is not None:
        if (
            db.query(Link)
            .filter(
                Link.project_id == link.project_id,
                Link.map_campaign_id == link.map_campaign_id,
            )
            .first()
            is not None
        ):
            raise HTTPException(status_code=400, detail="Link already exists")


@router.post("/", response_model=LinkSchema, status_code=201)
def create_link(link: LinkCreateSchema, db: Session = Depends(get_db)):
    """Create a link; any combination of project_id, initiative_id, map_campaign_id."""
    _validate_link_entities(link, db)
    _raise_if_link_duplicate(link, db)
    db_link = Link(
        project_id=link.project_id,
        initiative_id=link.initiative_id,
        map_campaign_id=link.map_campaign_id,
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


@router.get("/", response_model=list[LinkSchema])
def list_links(db: Session = Depends(get_db)):
    """Get all links."""
    links = db.query(Link).all()
    return links


@router.get("/{link_id}", response_model=LinkSchema)
def get_link(link_id: UUID, db: Session = Depends(get_db)):
    """Get a specific link by ID."""
    db_link = db.query(Link).filter(Link.id == link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    return db_link


@router.get("/project/{project_id}", response_model=list[LinkSchema])
def get_links_by_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get all links for a specific project."""
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    links = db.query(Link).filter(Link.project_id == project_id).all()
    return links


@router.get("/initiative/{initiative_id}", response_model=list[LinkSchema])
def get_links_by_initiative(initiative_id: UUID, db: Session = Depends(get_db)):
    """Get all links for a specific initiative."""
    # Validate initiative exists
    initiative = db.query(Initiative).filter(
        Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")

    links = db.query(Link).filter(Link.initiative_id == initiative_id).all()
    return links


def _validate_update_entities(update_data: dict, db: Session, db_link: Link) -> None:
    if update_data.get("project_id") is not None:
        if db.query(Project).filter(Project.id == update_data["project_id"]).first() is None:
            raise HTTPException(status_code=404, detail="Project not found")
    if update_data.get("initiative_id") is not None:
        if (
            db.query(Initiative).filter(Initiative.id ==
                                        update_data["initiative_id"]).first()
            is None
        ):
            raise HTTPException(status_code=404, detail="Initiative not found")
    if update_data.get("map_campaign_id") is not None:
        if (
            db.query(MapCampaign).filter(MapCampaign.id ==
                                         update_data["map_campaign_id"]).first()
            is None
        ):
            raise HTTPException(
                status_code=404, detail="Map campaign not found")


def _raise_if_update_link_duplicate(
    link_id: UUID,
    new_project_id: UUID | None,
    new_initiative_id: UUID | None,
    new_map_campaign_id: UUID | None,
    db: Session,
) -> None:
    if new_project_id is not None and new_initiative_id is not None:
        if (
            db.query(Link)
            .filter(
                Link.id != link_id,
                Link.project_id == new_project_id,
                Link.initiative_id == new_initiative_id,
            )
            .first()
            is not None
        ):
            raise HTTPException(status_code=400, detail="Link already exists")
    if new_project_id is not None and new_map_campaign_id is not None:
        if (
            db.query(Link)
            .filter(
                Link.id != link_id,
                Link.project_id == new_project_id,
                Link.map_campaign_id == new_map_campaign_id,
            )
            .first()
            is not None
        ):
            raise HTTPException(status_code=400, detail="Link already exists")


@router.patch("/{link_id}", response_model=LinkSchema)
def update_link(link_id: UUID, link: LinkUpdateSchema, db: Session = Depends(get_db)):
    """Update a link (change project and/or target)."""
    db_link = db.query(Link).filter(Link.id == link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    update_data = link.model_dump(exclude_unset=True)
    _validate_update_entities(update_data, db, db_link)
    new_project_id = update_data.get("project_id", db_link.project_id)
    new_initiative_id = update_data.get("initiative_id", db_link.initiative_id)
    new_map_campaign_id = update_data.get(
        "map_campaign_id", db_link.map_campaign_id)
    _raise_if_update_link_duplicate(
        link_id, new_project_id, new_initiative_id, new_map_campaign_id, db
    )
    for key, value in update_data.items():
        setattr(db_link, key, value)
    db.commit()
    db.refresh(db_link)
    return db_link


@router.delete("/{link_id}", response_model=LinkSchema)
def delete_link(link_id: UUID, db: Session = Depends(get_db)):
    """Delete a link."""
    db_link = db.query(Link).filter(Link.id == link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    out = LinkSchema.model_validate(db_link)
    db.delete(db_link)
    db.commit()
    return out
