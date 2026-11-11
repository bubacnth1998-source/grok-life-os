"""Grok LIFE OS — settings from environment only."""
from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "Grok LIFE OS"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default=False, validation_alias="LIFE_OS_DEBUG")
    ENVIRONMENT: str = Field(default="development", validation_alias="LIFE_OS_ENV")
    SECRET_KEY: str = Field(default="grok-life-os-dev-secret-change-in-production-32c", validation_alias="LIFE_OS_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, validation_alias="LIFE_OS_TOKEN_EXPIRE_MINUTES")
    DATABASE_URL: str = "sqlite:///./data/grok_life_os.db"
    VERCEL: bool = False
    CORS_ORIGINS: str = Field(default="", validation_alias="LIFE_OS_CORS_ORIGINS")
    MEDIA_PATH: str = Field(default="./data/media", validation_alias="LIFE_OS_MEDIA_PATH")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AI_PROVIDER: str = Field(default="auto", validation_alias="LIFE_OS_AI_PROVIDER")

    @model_validator(mode="after")
    def validate_security_settings(self):
        environment = self.ENVIRONMENT.strip().lower()
        if self.CORS_ORIGINS.strip() == "*":
            raise ValueError("Wildcard CORS is not allowed; configure explicit trusted origins")
        if environment in {"production", "prod"}:
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "grok-life-os-dev-secret-change-in-production-32c":
                raise ValueError("Production requires a unique LIFE_OS_SECRET_KEY of at least 32 characters")
        if self.VERCEL:
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "grok-life-os-dev-secret-change-in-production-32c":
                raise ValueError("Vercel requires a unique LIFE_OS_SECRET_KEY of at least 32 characters")
            normalized_db = self.DATABASE_URL.lower()
            if normalized_db.startswith("sqlite:"):
                raise ValueError("Vercel requires durable PostgreSQL storage; SQLite is not supported for persistent user data")
        return self

    @property
    def cors_list(self):
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    @property
    def llm_enabled(self):
        if self.AI_PROVIDER == "rules":
            return False
        return bool(self.OPENAI_API_KEY)


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
