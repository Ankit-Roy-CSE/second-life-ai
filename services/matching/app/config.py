from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_matching"
    redis_url: str = "redis://redis:6379/0"
    ai_mode: str = "mock"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    user_service_url: str = "http://user:8001"


settings = Settings()
