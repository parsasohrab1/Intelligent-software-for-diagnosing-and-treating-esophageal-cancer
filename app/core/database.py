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
    """Initialize database (create tables if not exist) and seed data if empty"""
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
        
        # Auto-seed data if database is empty (run in background thread to not block startup)
        import threading
        try:
            # Run in background thread to not block startup
            seed_thread = threading.Thread(
                target=_auto_seed_data_if_empty_sync,
                daemon=True,
                name="AutoSeedData"
            )
            seed_thread.start()
            logger.info("Auto-seeding thread started (checking database in background)...")
        except Exception as seed_err:
            logger.warning(f"Failed to start auto-seeding thread: {seed_err}")
            logger.warning("Dashboard may not have data. You can generate data manually.")
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


def _auto_seed_data_if_empty_sync():
    """Automatically seed data if database is empty (synchronous version)
    First tries to restore from saved snapshot, then generates new data if needed
    """
    import logging
    from app.models.patient import Patient
    from app.models.imaging_data import ImagingData
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check if data exists
        db = SessionLocal()
        try:
            patient_count = db.query(Patient).count()
            mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
            
            # If we have less than 10 patients or no MRI data, try to restore from snapshot
            if patient_count < 10 or mri_count < 10:
                logger.info("=" * 60)
                logger.info("Database is empty or has insufficient data.")
                logger.info(f"Current: {patient_count} patients, {mri_count} MRI images")
                logger.info("=" * 60)
                
                # Try to restore from saved snapshot first
                snapshot_path = Path("data_snapshot.json")
                if snapshot_path.exists():
                    logger.info("Found saved data snapshot. Restoring...")
                    try:
                        from scripts.restore_saved_data import restore_saved_data
                        if restore_saved_data(str(snapshot_path), clear_existing=True):
                            # Verify after restore
                            db.expire_all()
                            new_patient_count = db.query(Patient).count()
                            new_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
                            
                            if new_patient_count >= 10 and new_mri_count >= 10:
                                logger.info("=" * 60)
                                logger.info("✅ Data restored from snapshot!")
                                logger.info(f"   Patients: {new_patient_count}")
                                logger.info(f"   MRI Images: {new_mri_count}")
                                logger.info("   Dashboard is now ready with saved data!")
                                logger.info("=" * 60)
                                return
                            else:
                                logger.warning("Restored data insufficient. Will generate new data...")
                        else:
                            logger.warning("Failed to restore from snapshot. Will generate new data...")
                    except Exception as restore_err:
                        logger.warning(f"Error restoring from snapshot: {restore_err}")
                        logger.warning("Will generate new data...")
                else:
                    logger.info("No saved snapshot found. Will generate new data...")
                
                # If restore failed or no snapshot, generate synthetic data
                logger.info("Generating new synthetic data...")
                from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
                
                generator = EsophagealCancerSyntheticData(seed=42)
                
                # Generate data: 50 patients with 40% cancer ratio
                logger.info("Generating 50 patients with 40% cancer ratio...")
                dataset = generator.generate_all_data(
                    n_patients=50,
                    cancer_ratio=0.4
                )
                
                # Save to database
                logger.info("Saving data to database...")
                generator.save_to_database(dataset, db)
                db.commit()
                
                # Verify
                new_patient_count = db.query(Patient).count()
                new_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
                
                logger.info("=" * 60)
                logger.info("✅ Auto-seeding completed!")
                logger.info(f"   Patients: {new_patient_count}")
                logger.info(f"   MRI Images: {new_mri_count}")
                logger.info("   Dashboard is now ready with data!")
                logger.info("=" * 60)
            else:
                logger.info(f"✅ Database already has data: {patient_count} patients, {mri_count} MRI images")
        finally:
            db.close()
    except Exception as e:
        import traceback
        logger.error(f"❌ Auto-seeding failed: {e}")
        logger.error(traceback.format_exc())
        # Don't raise - let the app continue

