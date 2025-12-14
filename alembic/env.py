"""
Alembic environment configuration
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base
from app.core.config import settings

# Import all models to ensure they are registered
from app.models import (  # noqa: F401
    patient,
    clinical_data,
    genomic_data,
    imaging_data,
    treatment_data,
    lab_results,
    quality_of_life,
    user,
)

# Import compliance models
try:
    from app.core.compliance.validation_documentation import (  # noqa: F401
        ValidationProtocol,
        ValidationTestCase,
        ValidationExecution,
        ValidationResult,
    )
    from app.core.compliance.risk_management import (  # noqa: F401
        Risk,
        RiskControl,
    )
    from app.core.compliance.regulatory_tracking import (  # noqa: F401
        RegulatorySubmission,
        RegulatoryRequirement,
        RegulatoryDocument,
    )
    from app.core.compliance.quality_assurance import (  # noqa: F401
        QADocument,
        Audit,
        CAPA,
        NonConformance,
    )
    from app.core.compliance.change_control import (  # noqa: F401
        ChangeRequest,
        ChangeApproval,
        DeviceHistoryRecord,
    )
    from app.core.compliance.software_lifecycle import (  # noqa: F401
        SoftwareLifecycleRecord,
        SoftwareVersion,
        SoftwareChange,
    )
    from app.core.security.consent_manager import PatientConsent  # noqa: F401
    from app.services.training.training_system import (  # noqa: F401
        TrainingModule,
        TrainingEnrollment,
        TrainingQuiz,
    )
except ImportError as e:
    # Some models may not be available during migration
    pass

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

