"""
MongoDB configuration and client
"""
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional

from app.core.config import settings

# MongoDB client
_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def get_mongodb_client() -> Optional[MongoClient]:
    """Get MongoDB client instance (non-blocking)"""
    global _client
    if _client is None:
        try:
            # Use very short timeouts to prevent hanging on startup
            _client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=500,  # Very short timeout
                connectTimeoutMS=500,  # Very short timeout
                socketTimeoutMS=500,  # Socket timeout
                connect=False,  # Don't connect immediately
            )
            # Don't test connection here - let it fail gracefully when actually used
        except Exception as e:
            import logging
            logging.warning(f"MongoDB client creation failed: {e}")
            # MongoDB not available - set to None to prevent retries
            _client = None
    return _client


def get_mongodb_database() -> Optional[Database]:
    """Get MongoDB database instance"""
    global _database
    if _database is None:
        client = get_mongodb_client()
        if client is None:
            return None
        _database = client[settings.MONGODB_DB]
    return _database


def close_mongodb_connection():
    """Close MongoDB connection"""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None

