
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    frontend_url: str = "http://localhost:5173"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    refresh_token_expire_days: int = 30

settings = Settings()
