from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field  # Add this import
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
print(f"Env file exists: {env_path.exists()}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding='utf-8'
    )
    POSTMARK_API_TOKEN: str
    BASE_URL: str
    FRONTEND_BASE_URL: str
    RUNNING_ENV: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    DATABASE_REPORT_TABLE: str
    DATABASE_GRID_TABLE: str
    AIPDET_FE_SA_GCP: str = Field(max_length=10000)  # Adjust number as needed
    AIPDET_BE_SA_GCP: str = Field(max_length=10000)
    GEE_SA_GCP: str = Field(max_length=10000)


@lru_cache()
def get_settings():
    return Settings()
