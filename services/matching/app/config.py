"""
Config for the Hyperlocal Matching Service.
"""

from pydantic_settings import SettingsConfigDict
from shared_py.config.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "matching"
    database_url: str = (
        "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_matching"
    )

    # User Service base URL for candidate lookup
    user_service_url: str = "http://user:8001"

    # Matching thresholds
    match_radius_km: float = 50.0
    match_score_threshold: float = 0.4  # score > this → match found


settings = Settings()
