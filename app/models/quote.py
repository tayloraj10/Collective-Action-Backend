from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    text = Column(String, nullable=False)
    translation = Column(String, nullable=True)
    active = Column(Boolean, default=True)
