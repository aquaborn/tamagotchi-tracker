from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    debug: bool = False
    mistral_api_key: Optional[str] = None  # Для AI чата с питомцем

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()

# Singleton for easy import
settings = get_settings()