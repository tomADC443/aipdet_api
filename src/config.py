from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    POSTMARK_API_TOKEN: str
    BASE_URL: str
    FRONTEND_BASE_URL: str
    RUNNING_ENV: str
    JWT_SECRET: str
    JWT_ALGORITHM: str


@lru_cache()
def get_settings():
    return Settings()
