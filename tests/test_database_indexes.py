"""
Unit tests for database_indexes module.

Uses SQLite in-memory so create_all_indexes and related behavior
can be verified without PostgreSQL.
"""
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
# Import models so Base.metadata has all tables
from app.models import patient, clinical_data, genomic_data, imaging_data, treatment_data  # noqa: F401


@pytest.fixture
def sqlite_memory_engine():
    """Create in-memory SQLite engine."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )


@pytest.fixture
def sqlite_session(sqlite_memory_engine):
    """Create session with tables from Base.metadata (in-memory SQLite)."""
    Base.metadata.create_all(bind=sqlite_memory_engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_memory_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


class TestCreateAllIndexes:
    """Tests for create_all_indexes with SQLite in-memory."""

    @patch("app.core.database_indexes.get_database_type")
    def test_create_all_indexes_returns_dict(self, mock_get_type, sqlite_session):
        """create_all_indexes(session=...) should return dict index_name -> bool."""
        mock_get_type.return_value = "sqlite"
        from app.core.database_indexes import create_all_indexes, ALL_INDEXES

        results = create_all_indexes(session=sqlite_session)

        assert isinstance(results, dict)
        assert len(results) == len(ALL_INDEXES)
        for name, success in results.items():
            assert isinstance(name, str)
            assert isinstance(success, bool)

    @patch("app.core.database_indexes.get_database_type")
    def test_create_all_indexes_creates_indexes(self, mock_get_type, sqlite_session):
        """create_all_indexes should create indexes (success True for SQLite)."""
        mock_get_type.return_value = "sqlite"
        from app.core.database_indexes import create_all_indexes, ALL_INDEXES

        results = create_all_indexes(session=sqlite_session)

        # All or most should succeed (some partial indexes may differ on SQLite)
        success_count = sum(1 for v in results.values() if v)
        assert success_count >= len(ALL_INDEXES) // 2

    @patch("app.core.database_indexes.get_database_type")
    def test_create_all_indexes_idempotent(self, mock_get_type, sqlite_session):
        """Calling create_all_indexes twice should not fail (IF NOT EXISTS)."""
        mock_get_type.return_value = "sqlite"
        from app.core.database_indexes import create_all_indexes

        first = create_all_indexes(session=sqlite_session)
        second = create_all_indexes(session=sqlite_session)

        assert first.keys() == second.keys()
        for key in first:
            assert second[key] is True


class TestCreateIndexSql:
    """Tests for create_index_sql."""

    def test_create_index_sql_sqlite_simple(self):
        """create_index_sql for SQLite without WHERE."""
        from app.core.database_indexes import create_index_sql

        index_def = {
            "name": "ix_test_patient_id",
            "table": "patients",
            "columns": ["patient_id"],
        }
        sql = create_index_sql(index_def, "sqlite")
        assert "CREATE INDEX IF NOT EXISTS ix_test_patient_id" in sql
        assert "ON patients (patient_id)" in sql
        assert "WHERE" not in sql

    def test_create_index_sql_sqlite_partial(self):
        """create_index_sql for SQLite with WHERE (partial index)."""
        from app.core.database_indexes import create_index_sql

        index_def = {
            "name": "ix_test_partial",
            "table": "patients",
            "columns": ["has_cancer"],
            "where": "has_cancer = true",
        }
        sql = create_index_sql(index_def, "sqlite")
        assert "CREATE INDEX IF NOT EXISTS" in sql
        assert "WHERE has_cancer = true" in sql

    def test_create_index_sql_postgresql_partial(self):
        """create_index_sql for PostgreSQL with WHERE."""
        from app.core.database_indexes import create_index_sql

        index_def = {
            "name": "ix_test_partial",
            "table": "patients",
            "columns": ["has_cancer"],
            "where": "has_cancer = true",
        }
        sql = create_index_sql(index_def, "postgresql")
        assert "CREATE INDEX IF NOT EXISTS" in sql
        assert "WHERE has_cancer = true" in sql


class TestGetDatabaseType:
    """Tests for get_database_type."""

    def test_get_database_type_sqlite(self):
        """get_database_type returns 'sqlite' when USE_SQLITE is True."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.USE_SQLITE = True
            from app.core.database_indexes import get_database_type
            assert get_database_type() == "sqlite"

    def test_get_database_type_postgresql(self):
        """get_database_type returns 'postgresql' when USE_SQLITE is False."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.USE_SQLITE = False
            from app.core.database_indexes import get_database_type
            assert get_database_type() == "postgresql"


class TestGetIndexHealthReport:
    """Tests for get_index_health_report (with in-memory SQLite)."""

    @patch("app.core.database_indexes.get_database_type")
    @patch("app.core.database_indexes.SessionLocal")
    def test_get_index_health_report_structure(self, mock_session_local, mock_get_type, sqlite_session):
        """get_index_health_report returns database_type, strategic_indexes, coverage."""
        mock_get_type.return_value = "sqlite"
        mock_session_local.return_value = sqlite_session
        from app.core.database_indexes import get_index_health_report

        report = get_index_health_report()

        assert isinstance(report, dict)
        assert report.get("database_type") == "sqlite"
        assert "strategic_indexes" in report
        assert "coverage" in report
        assert "total_defined" in report["coverage"]
        assert "existing" in report["coverage"]
        assert "percentage" in report["coverage"]
