"""
Test database connections
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal
from app.core.redis_client import get_redis_client
from app.core.mongodb import get_mongodb_database


def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        db = SessionLocal()
        result = db.execute("SELECT 1").scalar()
        db.close()
        print("✅ PostgreSQL: Connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed - {str(e)}")
        return False


def test_mongodb():
    """Test MongoDB connection"""
    try:
        mongodb = get_mongodb_database()
        mongodb.command("ping")
        print("✅ MongoDB: Connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB: Connection failed - {str(e)}")
        return False


def test_redis():
    """Test Redis connection"""
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        print("✅ Redis: Connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis: Connection failed - {str(e)}")
        return False


if __name__ == "__main__":
    print("Testing database connections...\n")
    results = [
        test_postgresql(),
        test_mongodb(),
        test_redis(),
    ]

    if all(results):
        print("\n✅ All database connections successful!")
        sys.exit(0)
    else:
        print("\n❌ Some database connections failed!")
        sys.exit(1)

