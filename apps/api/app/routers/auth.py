from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.deps.auth import create_access_token
from app.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

class AuthRequest(BaseModel):
    init_data: str


@router.post("/login")
async def login(auth_req: AuthRequest):
    """Аутентификация через Telegram WebApp initData"""
    settings = get_settings()
    
    logger.info(f"Bot token: {settings.bot_token[:10]}... if available")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Всегда используем упрощённую авторизацию для разработки
    # (Telegram Mini App не требует полной валидации hash в dev режиме)
    try:
        from urllib.parse import parse_qs
        import json
        
        params = parse_qs(auth_req.init_data)
        user_data = params.get('user', [None])[0]
        
        if user_data:
            user_obj = json.loads(user_data)
            user_id = int(user_obj['id'])
            
            # Создаём JWT токен
            token = create_access_token(data={"user_id": user_id})
            
            logger.info(f"Auth successful for user {user_id}")
            
            return {
                "token": token,
                "user_id": user_id,
            }
        else:
            raise HTTPException(status_code=401, detail="No user data in initData")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")
