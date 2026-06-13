from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # JWT (verify tokens issued by user service)
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"

    # Upstream service URLs
    user_service_url: str = "http://user:8001"
    grading_service_url: str = "http://grading:8002"
    lifecycle_service_url: str = "http://lifecycle:8003"
    passport_service_url: str = "http://passport:8004"
    matching_service_url: str = "http://matching:8005"
    sustainability_service_url: str = "http://sustainability:8006"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # MinIO / S3
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "slmai-media"
    s3_region: str = "us-east-1"


settings = Settings()
