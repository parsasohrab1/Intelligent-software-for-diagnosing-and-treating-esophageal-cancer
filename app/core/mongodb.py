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
    """Get MongoDB client instance"""
    global _client
    if _client is None:
        try:
            # Use shorter timeouts to prevent hanging
            _client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=1000,  # Reduced from 2000
                connectTimeoutMS=1000,  # Reduced from 2000
                socketTimeoutMS=1000,  # Add socket timeout
            )
            # Test connection with timeout protection
            # Use ping with timeout to prevent hanging
            _client.admin.command('ping', maxTimeMS=1000)
        except Exception:
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

