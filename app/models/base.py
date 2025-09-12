from sqlalchemy import Column, DateTime, func, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
import uuid
import os

# Force String UUID for SQLite compatibility in deployment
DATABASE_URL = os.getenv("DATABASE_URL", "")
RAILWAY_ENV = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("NODE_ENV") == "production"

# Force SQLite mode for Railway deployment or if DATABASE_URL contains sqlite
USE_SQLITE = ("sqlite" in DATABASE_URL.lower()) or RAILWAY_ENV or (not DATABASE_URL)

if USE_SQLITE:
    # SQLite-compatible UUID for deployment/Railway
    UUID_TYPE = String(36)
    UUID_DEFAULT = lambda: str(uuid.uuid4())
    print(f"🔧 Using SQLite UUID mode - DATABASE_URL: {DATABASE_URL}")
else:
    # PostgreSQL UUID for full features
    try:
        from sqlalchemy.dialects.postgresql import UUID
        UUID_TYPE = UUID(as_uuid=True)
        UUID_DEFAULT = uuid.uuid4
        print(f"🔧 Using PostgreSQL UUID mode - DATABASE_URL: {DATABASE_URL}")
    except ImportError:
        UUID_TYPE = String(36)
        UUID_DEFAULT = lambda: str(uuid.uuid4())
        print(f"🔧 Fallback to String UUID mode - DATABASE_URL: {DATABASE_URL}")


class Base(DeclarativeBase):
    """Base model with common fields"""
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(UUID_TYPE, primary_key=True, default=UUID_DEFAULT)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# Export UUID_TYPE for other models
__all__ = ['Base', 'UUID_TYPE', 'UUID_DEFAULT']