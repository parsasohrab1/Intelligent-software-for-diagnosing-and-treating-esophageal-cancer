"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock
from app.main import app
from app.core.database import Base, get_db

# Test database URL (use in-memory SQLite for tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    # This would create a test user and return token
    # For now, return empty dict (tests will handle auth separately)
    return {}


@pytest.fixture(scope="function")
def mock_mongodb():
    """Mock MongoDB connection"""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__ = Mock(return_value=mock_collection)
    mock_db.admin = MagicMock()
    mock_db.admin.command = Mock(return_value={"ok": 1})
    mock_db.client = MagicMock()
    mock_db.client.server_info = Mock(return_value={"version": "6.0.0", "uptime": 3600})
    
    with patch("app.core.mongodb.get_mongodb_database", return_value=mock_db):
        yield mock_db


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis connection"""
    mock_redis_client = MagicMock()
    mock_redis_client.ping = Mock(return_value=True)
    mock_redis_client.get = Mock(return_value=None)
    mock_redis_client.set = Mock(return_value=True)
    mock_redis_client.setex = Mock(return_value=True)
    mock_redis_client.delete = Mock(return_value=1)
    mock_redis_client.keys = Mock(return_value=[])
    mock_redis_client.info = Mock(return_value={
        "redis_version": "7.0.0",
        "used_memory_human": "1M",
        "connected_clients": 1,
        "db0": {}
    })
    
    with patch("app.core.redis_client.get_redis_client", return_value=mock_redis_client):
        yield mock_redis_client


@pytest.fixture(scope="function")
def mock_model_registry():
    """Mock model registry MongoDB collection"""
    mock_collection = MagicMock()
    mock_collection.find_one = Mock(return_value=None)
    mock_collection.find = Mock(return_value=[])
    mock_collection.insert_one = Mock(return_value=Mock(inserted_id="test_id"))
    mock_collection.update_one = Mock(return_value=Mock(modified_count=1))
    mock_collection.delete_one = Mock(return_value=Mock(deleted_count=1))
    
    mock_db = MagicMock()
    mock_db.__getitem__ = Mock(return_value=mock_collection)
    mock_db.model_registry = mock_collection
    
    with patch("app.services.model_registry.get_mongodb_database", return_value=mock_db):
        yield mock_collection

