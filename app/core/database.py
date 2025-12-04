"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

# Database engine (PostgreSQL or SQLite)
if settings.USE_SQLITE:
    # SQLite engine (no connection pooling needed)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite requires this for multi-threading
        echo=settings.DEBUG,
    )
else:
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

        # Test connection first with timeout
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as conn_err:
            logger.warning(f"Database connection test failed: {conn_err}")
            logger.warning("App will continue but database operations may fail")
            return  # Exit early if connection fails
        
        # Create all tables
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        except Exception as create_err:
            logger.warning(f"Table creation failed: {create_err}")
            logger.warning("Tables may already exist or database is not accessible")
    except OperationalError as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Please make sure:")
        logger.warning("  1. Docker Desktop is running")
        logger.warning("  2. Docker services are started: docker-compose up -d")
        logger.warning("  3. PostgreSQL is ready (wait 10-15 seconds)")
        # Don't raise - let the app start but database operations will fail
        # This allows health checks to report the issue
    except Exception as e:
        logger.warning(f"Database initialization error: {e}")
        logger.warning("App will continue but database operations may fail")
        # Don't raise - let the app start

