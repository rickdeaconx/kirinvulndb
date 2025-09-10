from sqlalchemy import Column, DateTime, func, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
import uuid

try:
    from sqlalchemy.dialects.postgresql import UUID
    UUID_TYPE = UUID(as_uuid=True)
    UUID_DEFAULT = uuid.uuid4
except ImportError:
    UUID_TYPE = String(36)
    UUID_DEFAULT = lambda: str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base model with common fields"""
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(UUID_TYPE, primary_key=True, default=UUID_DEFAULT)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)