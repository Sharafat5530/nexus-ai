from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS AI Teammate Platform"
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./nexus_local_v2.db"

    JWT_SECRET_KEY: SecretStr = Field(min_length=32)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=480)

    ADMIN_PASSWORD: SecretStr = Field(min_length=12)

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()