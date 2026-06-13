from pydantic_settings import SettingsConfigDict
from shared_py.config.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "grading"
    database_url: str = "postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_grading"
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "slmai-media"


settings = Settings()
