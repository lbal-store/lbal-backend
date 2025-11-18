from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = Field(default="LBAL")
    environment: str = Field(default="development")
    secret_key: str
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7)
    jwt_algorithm: str = Field(default="HS256")
    database_url: str
    redis_url: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str | None = None
    rate_limit_per_minute: int = Field(default=60)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
