"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "INEsCape"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_PREFIX: str = "/api/v1"

    # Database - PostgreSQL (fallback to SQLite if not available)
    USE_SQLITE: bool = True  # Use SQLite for local development without Docker
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "inescape"
    POSTGRES_USER: str = "inescape_user"
    POSTGRES_PASSWORD: str = "inescape_password"
    SQLITE_DB_PATH: str = "data/inescape.db"  # SQLite database file path

    # Read replica (production): optional PostgreSQL read replica URL for read-only queries
    DATABASE_READ_REPLICA_URL: Optional[str] = None  # e.g. postgresql://user:pass@replica-host:5432/db

    # Query timeout (PostgreSQL only): prevent long-running queries from hanging connections (seconds)
    QUERY_TIMEOUT_SECONDS: int = 30

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.SQLITE_DB_PATH), exist_ok=True)
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Database - MongoDB
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "inescape_metadata"
    MONGODB_USER: str = "inescape_user"
    MONGODB_PASSWORD: str = "inescape_password"

    @property
    def MONGODB_URL(self) -> str:
        return (
            f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                f"{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Object Storage
    STORAGE_TYPE: str = "minio"
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "inescape-data"
    STORAGE_USE_SSL: bool = False

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    HASH_SALT: str = os.getenv("HASH_SALT", "inescape_salt_2024_change_in_production")

    # Rate limiting: disabled automatically for the test session (see tests/conftest.py)
    # to avoid the shared in-process limiter state leaking across unrelated tests.
    RATE_LIMIT_ENABLED: bool = True

    # HIPAA/GDPR Compliance Settings
    USE_AES256_ENCRYPTION: bool = True  # Use AES-256 for HIPAA compliance
    DATA_RETENTION_DAYS: int = 2555  # 7 years (HIPAA requirement)
    ENABLE_DATA_MASKING: bool = True  # Enable data masking based on role
    REQUIRE_CONSENT_FOR_ACCESS: bool = True  # Require consent for data access

    # External APIs
    TCGA_API_KEY: str = ""
    GEO_API_KEY: str = ""
    KAGGLE_USERNAME: str = ""
    KAGGLE_KEY: str = ""

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000

    # Message Queue (Kafka/RabbitMQ)
    MESSAGE_QUEUE_TYPE: str = "rabbitmq"  # Options: "kafka", "rabbitmq"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PATIENT_DATA: str = "patient-data"
    KAFKA_TOPIC_IMAGING_DATA: str = "imaging-data"
    KAFKA_TOPIC_ALERTS: str = "alerts"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_QUEUE_PATIENT_DATA: str = "patient_data"
    RABBITMQ_QUEUE_IMAGING_DATA: str = "imaging_data"
    RABBITMQ_QUEUE_ALERTS: str = "alerts"

    # Model Monitoring
    MODEL_MONITORING_ENABLED: bool = True
    DATA_DRIFT_THRESHOLD: float = 0.1  # Kolmogorov-Smirnov statistic threshold
    MODEL_DECAY_THRESHOLD: float = 0.05  # Performance degradation threshold
    MONITORING_WINDOW_SIZE: int = 1000  # Number of predictions to monitor
    MONITORING_CHECK_INTERVAL: int = 3600  # Check interval in seconds
    
    # GAN Model Configuration
    GAN_MODEL_PATH: str = "models/gan/final_model"  # Path to trained GAN model weights
    GAN_ENABLED: bool = True  # Enable GAN image generation

    # A/B Testing
    AB_TESTING_ENABLED: bool = True
    AB_TEST_DEFAULT_TRAFFIC_SPLIT: float = 0.5  # 50/50 split by default

    # Multi-Modality Processing
    MULTI_MODALITY_ENABLED: bool = True
    IMAGE_PROCESSING_BACKEND: str = "opencv"  # Options: "opencv", "pillow"
    TEXT_PROCESSING_BACKEND: str = "spacy"  # Options: "spacy", "nltk"
    MAX_IMAGE_SIZE_MB: int = 50
    SUPPORTED_IMAGE_FORMATS: List[str] = ["dicom", "nifti", "png", "jpg", "jpeg", "tiff"]
    
    # Real-Time Processing
    REALTIME_ENABLED: bool = True
    REALTIME_TARGET_FPS: int = 30
    REALTIME_MAX_LATENCY_MS: float = 200.0  # Maximum latency for endoscopy room
    REALTIME_BUFFER_SIZE: int = 5
    REALTIME_USE_GPU: bool = True
    REALTIME_USE_TPU: bool = False
    REALTIME_OPTIMIZATION_LEVEL: str = "high"  # low, medium, high
    
    # Clinical System Integration
    PACS_ENABLED: bool = True
    PACS_HOST: str = "localhost"
    PACS_PORT: int = 11112
    PACS_AE_TITLE: str = "INESCAPE"
    ENDOSCOPY_ENABLED: bool = True
    ENDOSCOPY_SYSTEM_TYPE: str = "generic"  # olympus, pentax, fujifilm, generic
    EHR_ENABLED: bool = True
    EHR_SYSTEM_TYPE: str = "generic_fhir"  # epic, cerner, generic_fhir
    EHR_FHIR_BASE_URL: str = ""
    EHR_USE_OAUTH: bool = True

    # Multi-level Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_L1_MAX_SIZE: int = 1000  # Maximum number of entries in L1 (memory) cache
    CACHE_L1_MAX_MEMORY_MB: int = 100  # Maximum memory for L1 cache in MB
    CACHE_DEFAULT_TTL: int = 3600  # Default TTL in seconds (1 hour)
    CACHE_COMPRESSION_ENABLED: bool = True
    CACHE_COMPRESSION_THRESHOLD: int = 1024  # Compress data larger than 1KB
    CACHE_COMPRESSION_ALGORITHM: str = "gzip"  # Options: "gzip", "zlib", "none"
    
    # Cache Warming Configuration
    CACHE_WARMING_ENABLED: bool = True
    CACHE_WARMING_INTERVAL: int = 1800  # Check interval in seconds (30 minutes)
    CACHE_WARMING_ON_STARTUP: bool = True  # Warm cache on application startup
    
    # Endpoint-specific cache TTLs
    CACHE_TTL_DASHBOARD: int = 300  # 5 minutes for dashboard
    CACHE_TTL_PATIENTS_LIST: int = 120  # 2 minutes for patients list
    CACHE_TTL_ML_MODELS: int = 600  # 10 minutes for ML models
    CACHE_TTL_STATISTICS: int = 900  # 15 minutes for statistics
    CACHE_TTL_IMAGING: int = 1800  # 30 minutes for imaging data

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Values that must never survive into production - if any of these are still
# set when ENVIRONMENT=="production", the app refuses to start.
_INSECURE_DEFAULTS = {
    "SECRET_KEY": "your-secret-key-change-in-production",
    "HASH_SALT": "inescape_salt_2024_change_in_production",
    "STORAGE_ACCESS_KEY": "minioadmin",
    "STORAGE_SECRET_KEY": "minioadmin",
    "RABBITMQ_USER": "guest",
    "RABBITMQ_PASSWORD": "guest",
}


def _validate_production_settings(s: "Settings") -> None:
    """Fail fast if production is about to start with insecure defaults."""
    if s.ENVIRONMENT != "production":
        return

    problems = [
        field for field, insecure_value in _INSECURE_DEFAULTS.items()
        if getattr(s, field) == insecure_value
    ]
    if not s.ENCRYPTION_KEY:
        problems.append("ENCRYPTION_KEY (empty)")
    if s.DEBUG:
        problems.append("DEBUG (must be False)")

    if problems:
        raise RuntimeError(
            "Refusing to start with ENVIRONMENT=production while using insecure "
            f"default configuration for: {', '.join(problems)}. "
            "Set proper values via environment variables before deploying."
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    s = Settings()
    _validate_production_settings(s)
    return s


settings = get_settings()

