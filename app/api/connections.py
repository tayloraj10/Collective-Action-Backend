from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreateSchema,
    ConnectionSchema,
    ConnectionSummarySchema,
    ConnectionWithUserSchema,
    PreviewUserSchema,
    infer_connection_type,
)

router = APIRouter(prefix="/connections", tags=["connections"])

_VALID_FROM_TYPES = {"user", "directory_of_good"}
_VALID_TO_TYPES = {"initiative", "directory_of_good"}


def _preview_user(user: User | None) -> PreviewUserSchema | None:
    if user is None:
        return None
    return PreviewUserSchema(id=user.id, name=user.name, photo_url=user.photo_url)


@router.post("/", response_model=ConnectionSchema, status_code=201)
def create_connection(body: ConnectionCreateSchema, db: Session = Depends(get_db)):
    if body.from_type not in _VALID_FROM_TYPES:
        raise HTTPException(400, f"from_type must be one of {_VALID_FROM_TYPES}")
    if body.to_type not in _VALID_TO_TYPES:
        raise HTTPException(400, f"to_type must be one of {_VALID_TO_TYPES}")

    creator = db.query(User).filter(User.id == body.created_by).first()
    if not creator:
        raise HTTPException(404, f"User {body.created_by} not found")

    existing = (
        db.query(Connection)
        .filter(
            Connection.from_type == body.from_type,
            Connection.from_id == body.from_id,
            Connection.to_type == body.to_type,
            Connection.to_id == body.to_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(409, "Connection already exists")

    conn = Connection(
        **body.model_dump(),
        connection_type=infer_connection_type(body.from_type, body.to_type),
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/{connection_id}", status_code=204)
def delete_connection(
    connection_id: UUID,
    user_id: UUID = Query(..., description="ID of the user requesting deletion"),
    db: Session = Depends(get_db),
):
    conn = db.query(Connection).filter(Connection.id == connection_id).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    if str(conn.created_by) != str(user_id):
        raise HTTPException(403, "Not authorized to delete this connection")
    db.delete(conn)
    db.commit()
    return None


@router.get("/entity/{to_type}/{to_id}", response_model=list[ConnectionWithUserSchema])
def get_connections_for_entity(
    to_type: str,
    to_id: UUID,
    connection_type: str | None = Query(None, description="Filter by connection_type"),
    db: Session = Depends(get_db),
):
    """All connections to a specific entity, optionally filtered by type."""
    q = db.query(Connection).filter(
        Connection.to_type == to_type,
        Connection.to_id == to_id,
    )
    if connection_type:
        q = q.filter(Connection.connection_type == connection_type)
    connections = q.order_by(Connection.created_at).all()

    result = []
    for conn in connections:
        user = db.query(User).filter(User.id == conn.created_by).first()
        result.append(
            ConnectionWithUserSchema(
                id=conn.id,
                created_by=conn.created_by,
                from_type=conn.from_type,
                from_id=conn.from_id,
                to_type=conn.to_type,
                to_id=conn.to_id,
                connection_type=conn.connection_type,
                created_at=conn.created_at,
                user=_preview_user(user),
            )
        )
    return result


@router.get("/user/{user_id}", response_model=list[ConnectionSchema])
def get_connections_for_user(
    user_id: UUID,
    connection_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """All connections created by a specific user, optionally filtered by type."""
    q = db.query(Connection).filter(Connection.created_by == user_id)
    if connection_type:
        q = q.filter(Connection.connection_type == connection_type)
    return q.order_by(Connection.created_at).all()


@router.get("/summary/{to_type}", response_model=list[ConnectionSummarySchema])
def get_connection_summary(to_type: str, db: Session = Depends(get_db)):
    """
    Aggregated connection counts + avatar previews for every entity of `to_type`.
    One request covers all cards on the Connect screen.
    """
    if to_type not in _VALID_TO_TYPES:
        raise HTTPException(400, f"to_type must be one of {_VALID_TO_TYPES}")

    connections = (
        db.query(Connection)
        .filter(Connection.to_type == to_type)
        .order_by(Connection.created_at)
        .all()
    )

    grouped: dict[str, list[Connection]] = {}
    for conn in connections:
        grouped.setdefault(str(conn.to_id), []).append(conn)

    result = []
    for to_id_str, conns in grouped.items():
        user_conns = [c for c in conns if c.from_type == "user"]
        org_conns = [c for c in conns if c.from_type == "directory_of_good"]

        preview_users: list[PreviewUserSchema] = []
        for uc in user_conns[:4]:
            user = db.query(User).filter(User.id == uc.created_by).first()
            if user:
                preview_users.append(
                    PreviewUserSchema(id=user.id, name=user.name, photo_url=user.photo_url)
                )

        result.append(
            ConnectionSummarySchema(
                to_id=UUID(to_id_str),
                total_count=len(conns),
                user_count=len(user_conns),
                org_count=len(org_conns),
                preview_users=preview_users,
                org_ids=[c.from_id for c in org_conns],
            )
        )

    return result
