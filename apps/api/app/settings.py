from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")

def get_settings():
    return Settings()