from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_sustainability"
    )
    redis_url: str = "redis://redis:6379/0"


settings = Settings()
