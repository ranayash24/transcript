from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/vsi"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # MinIO (S3-compatible, free self-hosted storage)
    minio_endpoint_url: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "video-scene-intelligence"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "video_segments"

    # Google Gemini (free tier — 1,500 requests/day)
    gemini_api_key: str = ""

    # Whisper (runs locally, free)
    whisper_model: str = "base"  # base | medium | large-v3

    # Pipeline tuning
    frame_interval_seconds: int = 5
    scene_change_threshold: float = 0.4
    segment_window_seconds: int = 15
    max_video_size_mb: int = 500
    signed_url_expiry_hours: int = 6

    # Security
    api_secret_key: str = "change-me-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
