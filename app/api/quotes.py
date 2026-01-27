from app.schemas.quote import QuoteSchema, QuoteCreateSchema
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.models.quote import Quote

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteSchema)
def create_quote(quote: QuoteCreateSchema, db: Session = Depends(get_db)):
    db_quote = Quote(**quote.dict())
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote


@router.get("/", response_model=list[QuoteSchema])
def list_quotes(db: Session = Depends(get_db)):
    return db.query(Quote).all()


@router.get("/random", response_model=QuoteSchema)
def get_random_quote(db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(
        Quote.active == True).order_by(func.random()).first()
    if not quote:
        raise HTTPException(status_code=404, detail="No active quotes found")
    return quote


@router.get("/{quote_id}", response_model=QuoteSchema)
def get_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.patch("/{quote_id}", response_model=QuoteSchema)
def update_quote(quote_id: UUID, quote_update: QuoteCreateSchema, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    for field, value in quote_update.dict(exclude_unset=True).items():
        setattr(quote, field, value)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    db.delete(quote)
    db.commit()
    return None


router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteSchema)
def create_quote(quote: QuoteCreateSchema, db: Session = Depends(get_db)):
    db_quote = Quote(**quote.dict())
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote


@router.get("/", response_model=list[QuoteSchema])
def list_quotes(db: Session = Depends(get_db)):
    return db.query(Quote).all()


@router.get("/random", response_model=QuoteSchema)
def get_random_quote(db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(
        Quote.active == True).order_by(func.random()).first()
    if not quote:
        raise HTTPException(status_code=404, detail="No active quotes found")
    return quote


@router.get("/{quote_id}", response_model=QuoteSchema)
def get_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.patch("/{quote_id}", response_model=QuoteSchema)
def update_quote(quote_id: UUID, quote_update: QuoteCreateSchema, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    for field, value in quote_update.dict(exclude_unset=True).items():
        setattr(quote, field, value)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    db.delete(quote)
    db.commit()
    return None
