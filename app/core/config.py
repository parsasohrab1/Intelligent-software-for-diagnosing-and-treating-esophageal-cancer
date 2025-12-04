"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "INEsCape"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
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

    # A/B Testing
    AB_TESTING_ENABLED: bool = True
    AB_TEST_DEFAULT_TRAFFIC_SPLIT: float = 0.5  # 50/50 split by default

    # Multi-Modality Processing
    MULTI_MODALITY_ENABLED: bool = True
    IMAGE_PROCESSING_BACKEND: str = "opencv"  # Options: "opencv", "pillow"
    TEXT_PROCESSING_BACKEND: str = "spacy"  # Options: "spacy", "nltk"
    MAX_IMAGE_SIZE_MB: int = 50
    SUPPORTED_IMAGE_FORMATS: List[str] = ["dicom", "nifti", "png", "jpg", "jpeg", "tiff"]

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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

