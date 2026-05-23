from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Zameen Real Estate API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Professional Real Estate Platform API"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./zameen.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"


settings = Settings()
