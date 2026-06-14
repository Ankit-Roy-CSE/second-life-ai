from pydantic_settings import SettingsConfigDict

from shared_py.config.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "passport"
    database_url: str = "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_passport"

    # User service URL for future cross-service reads (matching stage)
    user_service_url: str = "http://user:8001"


settings = Settings()
