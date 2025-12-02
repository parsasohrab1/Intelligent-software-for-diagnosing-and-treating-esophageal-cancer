"""
Initialize database - create tables and initial data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine
from app.core.config import settings


def init_database():
    """Initialize database tables"""
    print("Initializing database...")
    print(f"Database URL: {settings.DATABASE_URL}")

    # Import all models to ensure they are registered
    from app.models import (  # noqa: F401
        patient,
        clinical_data,
        genomic_data,
        imaging_data,
        treatment_data,
        lab_results,
        quality_of_life,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    init_database()

