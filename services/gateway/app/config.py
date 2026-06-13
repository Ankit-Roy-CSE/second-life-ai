from pydantic_settings import SettingsConfigDict
from shared_py.config.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "gateway"

    # JWT — gateway verifies tokens issued by user service
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"

    # Upstream service URLs (Docker Compose service hostnames by default)
    user_service_url: str = "http://user:8001"
    grading_service_url: str = "http://grading:8002"
    lifecycle_service_url: str = "http://lifecycle:8003"
    passport_service_url: str = "http://passport:8004"
    matching_service_url: str = "http://matching:8005"
    sustainability_service_url: str = "http://sustainability:8006"

    # MinIO / S3 (gateway handles media upload)
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "slmai-media"
    s3_region: str = "us-east-1"


settings = Settings()
