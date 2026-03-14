from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )
    
    # ✅ Обязательные поля
    bot_token: str
    database_url: str  # From DATABASE_URL env var
    
    # Админы (Telegram IDs)
    admin_ids: List[int] = [84481976]


# ✅ Экземпляр на уровне модуля
settings = Settings()


# ✅ Опционально: функция для совместимости
def get_settings():
    return settings