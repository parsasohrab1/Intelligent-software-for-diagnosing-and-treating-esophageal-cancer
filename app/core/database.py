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
    import logging
    from sqlalchemy.exc import OperationalError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import all models here to ensure they are registered
        from app.models import (  # noqa: F401
            patient,
            clinical_data,
            genomic_data,
            imaging_data,
            treatment_data,
        )

        # Test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Please make sure:")
        logger.error("  1. Docker Desktop is running")
        logger.error("  2. Docker services are started: docker-compose up -d")
        logger.error("  3. PostgreSQL is ready (wait 10-15 seconds)")
        # Don't raise - let the app start but database operations will fail
        # This allows health checks to report the issue
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't raise - let the app start

