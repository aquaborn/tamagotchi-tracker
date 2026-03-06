from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )
    
    # ✅ Обязательные поля
    bot_token: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/tamagotchi"
    
    # Админы (Telegram IDs)
    admin_ids: List[int] = [84481976]
    internal_api_token: Optional[str] = None


# ✅ Экземпляр на уровне модуля
settings = Settings()


# ✅ Опционально: функция для совместимости
def get_settings():
    return settings
