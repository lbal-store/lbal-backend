from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    project_name: str = "LBAL"
    environment: str = "development"
    secret_key: str
    access_token_expire_minutes: int = 30
    database_url: str
    redis_url: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str | None = None
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
