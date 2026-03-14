"""
TON Connect & Token Mining API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
import re

from app.deps.db import get_db
from app.deps.auth import get_current_user_id
from app.models.user import User
from app.models.pet import PetModel as Pet

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ton", tags=["ton"])

# === Конфиг токеномики ===
TOKEN_CONFIG = {
    "name": "$PIXEL",
    "symbol": "PIXEL",
    
    # Пассивный майнинг (токены в час)
    "base_mining_rate": 10,  # Базовая скорость
    "level_bonus": 5,        # +5 за каждый уровень питомца
    "max_offline_hours": 24, # Максимум офлайн накопления
    
    # Активные награды
    "rewards": {
        "feed": 5,           # За кормление
        "play": 10,          # За игру
        "wash": 8,           # За купание
        "heal": 15,          # За лечение
        "daily_login": 50,   # Ежедневный бонус
        "streak_bonus": 10,  # За каждый день стрика
        "level_up": 100,     # За повышение уровня
        "achievement": 200,  # За достижение
        "referral": 500,     # За реферала
    },
    
    # Буст от счастья питомца
    "happiness_boost": {
        80: 1.5,   # 80%+ счастья = x1.5
        50: 1.2,   # 50%+ = x1.2
        0: 1.0     # базовый
    },
    
    # Airdrop фаза
    "airdrop_announced": False,
    "total_airdrop_pool": 1_000_000_000,  # 1 млрд токенов
}


# === Pydantic Models ===
class WalletConnectRequest(BaseModel):
    address: str = Field(..., min_length=40, max_length=128)
    
class TokenClaimRequest(BaseModel):
    amount: Optional[int] = Field(None, gt=0)


# === Helper Functions ===
def validate_ton_address(address: str) -> bool:
    """Валидация TON адреса"""
    # Raw address: 0:abc123... (66 chars)
    # Friendly: EQ... или UQ... (48 chars)
    if re.match(r'^0:[a-fA-F0-9]{64}$', address):
        return True
    if re.match(r'^[EU]Q[A-Za-z0-9_-]{46}$', address):
        return True
    return False

def calculate_mining_rate(pet_level: int, happiness: int) -> int:
    """Расчёт скорости майнинга"""
    base = TOKEN_CONFIG["base_mining_rate"]
    level_bonus = TOKEN_CONFIG["level_bonus"] * pet_level
    
    # Буст от счастья
    boost = 1.0
    for threshold, multiplier in sorted(TOKEN_CONFIG["happiness_boost"].items(), reverse=True):
        if happiness >= threshold:
            boost = multiplier
            break
    
    return int((base + level_bonus) * boost)

def calculate_offline_tokens(pet, last_tick: datetime) -> int:
    """Расчёт накопленных офлайн токенов"""
    if not last_tick:
        return 0
    
    now = datetime.now(timezone.utc)
    hours_offline = (now - last_tick).total_seconds() / 3600
    hours_offline = min(hours_offline, TOKEN_CONFIG["max_offline_hours"])
    
    if hours_offline < 0.1:  # Меньше 6 минут - не считаем
        return 0
    
    rate = calculate_mining_rate(pet.level, pet.happiness)
    return int(hours_offline * rate)


async def get_or_create_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# === API Endpoints ===

@router.get("/wallet")
async def get_wallet_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Статус подключения кошелька"""
    user = await get_or_create_user(user_id, db)
    
    return {
        "connected": user.wallet_address is not None,
        "address": user.wallet_address,
        "connected_at": user.wallet_connected_at.isoformat() if user.wallet_connected_at else None,
        "can_claim": user.wallet_address is not None and user.token_balance > 0
    }


@router.post("/wallet/connect")
async def connect_wallet(
    request: WalletConnectRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Подключить TON кошелёк"""
    if not validate_ton_address(request.address):
        raise HTTPException(status_code=400, detail="Неверный формат TON адреса")
    
    user = await get_or_create_user(user_id, db)
    
    # Проверяем не занят ли адрес
    existing = await db.execute(
        select(User).where(
            User.wallet_address == request.address,
            User.id != user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот кошелёк уже привязан к другому аккаунту")
    
    old_address = user.wallet_address
    user.wallet_address = request.address
    user.wallet_connected_at = datetime.now(timezone.utc)
    
    # Бонус за первое подключение
    bonus = 0
    if not old_address:
        bonus = 1000  # 1000 токенов за подключение кошелька
        user.token_balance += bonus
    
    await db.commit()
    
    logger.info(f"Wallet connected: user {user_id} -> {request.address}")
    
    return {
        "success": True,
        "address": request.address,
        "bonus_tokens": bonus,
        "message": f"✅ Кошелёк подключен!" + (f" Бонус: +{bonus} {TOKEN_CONFIG['symbol']}!" if bonus else "")
    }


@router.post("/wallet/disconnect")
async def disconnect_wallet(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Отключить кошелёк"""
    user = await get_or_create_user(user_id, db)
    
    if not user.wallet_address:
        raise HTTPException(status_code=400, detail="Кошелёк не подключен")
    
    user.wallet_address = None
    user.wallet_connected_at = None
    await db.commit()
    
    return {"success": True, "message": "Кошелёк отключен"}


@router.get("/tokens")
async def get_token_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Баланс токенов и статистика майнинга"""
    user = await get_or_create_user(user_id, db)
    
    # Получаем питомца для расчёта скорости
    result = await db.execute(select(Pet).where(Pet.user_id == user.id))
    pet = result.scalar_one_or_none()
    
    mining_rate = 0
    pending_tokens = 0
    
    if pet:
        mining_rate = calculate_mining_rate(pet.level, pet.happiness)
        pending_tokens = calculate_offline_tokens(pet, pet.last_tick_at)
    
    return {
        "token": TOKEN_CONFIG["symbol"],
        "balance": user.token_balance,
        "pending": pending_tokens,  # Ещё не собранные офлайн токены
        "total_earned": user.token_balance + user.token_claimed,
        "total_claimed": user.token_claimed,
        
        "mining": {
            "rate_per_hour": mining_rate,
            "max_offline_hours": TOKEN_CONFIG["max_offline_hours"],
            "pet_level": pet.level if pet else 0,
            "happiness_boost": calculate_mining_rate(pet.level if pet else 1, pet.happiness if pet else 50) / calculate_mining_rate(pet.level if pet else 1, 0) if pet else 1.0
        },
        
        "rewards": TOKEN_CONFIG["rewards"],
        
        "airdrop": {
            "announced": TOKEN_CONFIG["airdrop_announced"],
            "total_pool": TOKEN_CONFIG["total_airdrop_pool"],
            "your_share_estimate": user.token_balance  # Примерная доля
        },
        
        "wallet_connected": user.wallet_address is not None
    }


@router.post("/tokens/collect")
async def collect_offline_tokens(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Собрать накопленные офлайн токены"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(select(Pet).where(Pet.user_id == user.id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(status_code=400, detail="Нет питомца")
    
    tokens = calculate_offline_tokens(pet, pet.last_tick_at)
    
    if tokens < 1:
        return {
            "success": False,
            "collected": 0,
            "message": "Ещё нечего собирать! Подожди немного."
        }
    
    user.token_balance += tokens
    # last_tick_at обновляется в pet state endpoint
    
    await db.commit()
    
    logger.info(f"Tokens collected: user {user_id} got {tokens} {TOKEN_CONFIG['symbol']}")
    
    return {
        "success": True,
        "collected": tokens,
        "new_balance": user.token_balance,
        "message": f"⛏️ Собрано {tokens} {TOKEN_CONFIG['symbol']}!"
    }


@router.post("/tokens/claim")
async def claim_tokens_to_wallet(
    request: TokenClaimRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Вывести токены на кошелёк (будет работать после листинга)
    Пока просто записывает намерение
    """
    user = await get_or_create_user(user_id, db)
    
    if not user.wallet_address:
        raise HTTPException(status_code=400, detail="Сначала подключите кошелёк!")
    
    amount = request.amount or user.token_balance
    
    if amount > user.token_balance:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно токенов! Баланс: {user.token_balance}"
        )
    
    min_claim = 10000  # Минимум для вывода
    if amount < min_claim:
        raise HTTPException(
            status_code=400,
            detail=f"Минимум для вывода: {min_claim} {TOKEN_CONFIG['symbol']}"
        )
    
    # Пока airdrop не анонсирован - просто сохраняем
    if not TOKEN_CONFIG["airdrop_announced"]:
        return {
            "success": False,
            "message": "⏳ Вывод будет доступен после листинга токена! Продолжай копить.",
            "balance": user.token_balance,
            "airdrop_announced": False
        }
    
    # Когда будет листинг - тут будет реальный вывод через смарт-контракт
    user.token_balance -= amount
    user.token_claimed += amount
    user.token_last_claim = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "success": True,
        "claimed": amount,
        "new_balance": user.token_balance,
        "total_claimed": user.token_claimed,
        "message": f"✅ {amount} {TOKEN_CONFIG['symbol']} отправлены на {user.wallet_address[:8]}...!"
    }


@router.get("/leaderboard")
async def token_leaderboard(
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Топ майнеров"""
    result = await db.execute(
        select(User)
        .where(User.token_balance > 0)
        .order_by(User.token_balance.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    
    leaderboard = []
    for i, user in enumerate(users, 1):
        leaderboard.append({
            "rank": i,
            "username": user.username or f"Miner #{user.telegram_id % 10000}",
            "tokens": user.token_balance,
            "level": user.level,
            "wallet_connected": user.wallet_address is not None
        })
    
    # Общая статистика
    total_result = await db.execute(
        select(func.sum(User.token_balance), func.count(User.id))
        .where(User.token_balance > 0)
    )
    total_tokens, total_miners = total_result.one()
    
    return {
        "leaderboard": leaderboard,
        "stats": {
            "total_mined": total_tokens or 0,
            "total_miners": total_miners or 0,
            "airdrop_pool": TOKEN_CONFIG["total_airdrop_pool"]
        }
    }


# === Функция для начисления токенов за действия ===
async def reward_tokens(user: User, action: str, db: AsyncSession, multiplier: float = 1.0) -> int:
    """
    Начислить токены за действие.
    Вызывается из других роутеров.
    """
    if action not in TOKEN_CONFIG["rewards"]:
        return 0
    
    amount = int(TOKEN_CONFIG["rewards"][action] * multiplier)
    user.token_balance += amount
    # commit делается в вызывающем коде
    
    return amount
