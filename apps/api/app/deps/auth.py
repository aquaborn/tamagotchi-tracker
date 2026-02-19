from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Header, HTTPException, Depends
from jwt import PyJWTError
from pydantic_settings import BaseSettings, SettingsConfigDict

# ✅ Правильный отдельный импорт
from packages.core.core.security.tma_init_data import (
    validate_and_parse_init_data,
    TmaInitData,
    TmaAuthError,  # ✅ Добавлено в импорт, а не висит отдельно
)


class Settings(BaseSettings):
    # ✅ Только model_config для Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )
    
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


# Глобальный экземпляр настроек
settings = Settings()


# JWT Configuration
def get_jwt_settings():
    return {
        "secret_key": settings.jwt_secret_key,
        "algorithm": settings.jwt_algorithm,
        "access_token_expire_minutes": settings.access_token_expire_minutes,
    }


def create_access_token(data: dict, expires_delta: timedelta = None):
    jwt_settings = get_jwt_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=jwt_settings["access_token_expire_minutes"]
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        jwt_settings["secret_key"], 
        algorithm=jwt_settings["algorithm"]
    )
    return encoded_jwt


def get_current_user_id(
    authorization: Optional[str] = Header(default=None)
) -> int:
    """Получает ID пользователя из JWT-токена."""
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header is required"
        )
    
    try:
        # Убираем префикс "Bearer " если есть
        token = authorization.replace("Bearer ", "")
        
        jwt_settings = get_jwt_settings()
        payload = jwt.decode(
            token,
            jwt_settings["secret_key"],
            algorithms=[jwt_settings["algorithm"]]
        )
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: user_id not found"
            )
        
        return int(user_id)
        
    except PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )