from pydantic_settings import SettingsConfigDict
from shared_py.config.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "user"

    database_url: str = "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_user"
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440


settings = Settings()
