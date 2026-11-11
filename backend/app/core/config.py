"""Grok LIFE OS — settings from environment only."""
from functools import lru_cache
from typing import Optional
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Grok LIFE OS"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("LIFE_OS_DEBUG", "true").lower() in ("1", "true", "yes")
    ENVIRONMENT: str = os.getenv("LIFE_OS_ENV", "development")
    SECRET_KEY: str = os.getenv("LIFE_OS_SECRET_KEY", "grok-life-os-dev-secret-change-in-production-32c")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("LIFE_OS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////tmp/grok_life_os.db")
    CORS_ORIGINS: str = os.getenv("LIFE_OS_CORS_ORIGINS", "*")
    MEDIA_PATH: str = os.getenv("LIFE_OS_MEDIA_PATH", "/tmp/grok_life_os_media")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AI_PROVIDER: str = os.getenv("LIFE_OS_AI_PROVIDER", "auto")
    class Config:
        env_file = ".env"
        extra = "ignore"
    @property
    def cors_list(self):
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
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
