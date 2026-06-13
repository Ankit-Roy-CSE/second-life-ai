"""
Base settings for all Amazon Second Life AI backend services.

Each service subclasses BaseServiceSettings and adds its own fields:

    class Settings(BaseServiceSettings):
        database_url: str = "postgresql+asyncpg://..."
        my_extra: str = "value"

    settings = Settings()

All values are read from environment variables (or .env file).
Defaults point at local Docker Compose hostnames so services work
out-of-the-box with `docker compose up`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """
    Shared env-var settings inherited by every backend service.
    Service-specific settings classes add their own fields on top.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore unknown vars — services share one .env
    )

    # ── Service identity ──────────────────────────────────────────────────────
    service_name: str = "unknown-service"
    log_level: str = "INFO"

    # ── Redis (event bus) ─────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── AI mode ───────────────────────────────────────────────────────────────
    # mock = deterministic, no network, no AWS keys (default / CI)
    # aws  = real Bedrock + Rekognition
    # hybrid = Rekognition vision + Bedrock reasoning, mock the rest
    ai_mode: str = "mock"

    # ── AWS (only needed when ai_mode != "mock") ──────────────────────────────
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # ── CORS (comma-separated origins, used by Gateway) ──────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Split the comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
