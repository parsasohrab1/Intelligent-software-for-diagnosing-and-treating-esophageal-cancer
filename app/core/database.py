"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

# PostgreSQL engine with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,  # Increased from 10
    max_overflow=40,  # Increased from 20
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    echo=settings.DEBUG,
    connect_args={
        "connect_timeout": 10,
        "application_name": "inescape_api",
    },
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database (create tables if not exist)"""
    # Import all models here to ensure they are registered
    from app.models import (  # noqa: F401
        patient,
        clinical_data,
        genomic_data,
        imaging_data,
        treatment_data,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

