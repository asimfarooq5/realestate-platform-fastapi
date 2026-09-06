from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Malkiyat Real Estate API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Professional Real Estate Platform API"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./malkiyat.db"

    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    # No refresh-token flow exists yet, so the access token itself carries
    # the session — 30 days keeps mobile users logged in between app opens
    # instead of getting silently 401'd mid-session.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Rate limiting
    LOGIN_RATE_LIMIT: int = 5  # attempts
    LOGIN_RATE_WINDOW: int = 300  # seconds

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate()

    def _validate(self):
        secret = self.SECRET_KEY or os.environ.get("SECRET_KEY", "")
        if not secret or len(secret) < 32:
            raise RuntimeError(
                "SECRET_KEY must be set in the environment and be at least 32 "
                "characters long. Generate one with: openssl rand -hex 32"
            )
        if secret == "your-secret-key-here-change-in-production":
            raise RuntimeError("SECRET_KEY is still set to the insecure default value.")
        self.SECRET_KEY = secret


settings = Settings()
