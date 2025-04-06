from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dynamic Questionnaire API"
    API_V1_STR: str = "/api"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = "sqlite:///./dynamic_questionnaire.db"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
