from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.deps.auth import create_access_token
from app.settings import get_settings
from packages.core.core.security.tma_init_data import (
    validate_and_parse_init_data,
    TmaAuthError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

class AuthRequest(BaseModel):
    init_data: str


@router.post("/login")
async def login(auth_req: AuthRequest):
    """Аутентификация через Telegram WebApp initData"""
    settings = get_settings()

    try:
        parsed = validate_and_parse_init_data(
            init_data_raw=auth_req.init_data,
            bot_token=settings.bot_token,
            expires_in_sec=3600,
        )
        user_id = parsed.user.id
        token = create_access_token(data={"user_id": user_id})
        logger.info("Auth successful for user %s", user_id)
        return {
            "token": token,
            "user_id": user_id,
        }
    except TmaAuthError:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")
    except Exception:
        logger.exception("Auth error")
        raise HTTPException(status_code=401, detail="Auth failed")
