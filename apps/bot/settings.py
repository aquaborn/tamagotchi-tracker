from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )
    
    # ✅ Обязательные поля
    bot_token: str


# ✅ Экземпляр на уровне модуля
settings = Settings()


# ✅ Опционально: функция для совместимости
def get_settings():
    return settings