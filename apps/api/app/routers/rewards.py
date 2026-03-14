from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.deps.auth import get_current_user_id, require_internal_api_token
from app.deps.db import get_db
from app.models.user import User, VPNConfig, Achievement
from app.services.vpn_rewards import (
    generate_referral_code,
    generate_amnezia_config,
    REWARDS,
    XP_REWARDS,
    calculate_new_level,
    check_streak,
    ACHIEVEMENTS,
)
from app.i18n import get_text, get_available_languages, detect_language
from app.services.pet_types import (
    get_pet_by_id, get_free_pets, get_premium_pets, 
    is_pet_free, get_pet_price, ALL_PETS, FREE_PETS
)
from app.services.weather import (
    get_current_weather, get_shelter_info, get_next_shelter_upgrade,
    calculate_weather_effects, should_pet_hide, get_all_shelter_levels,
    SHELTER_LEVELS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/rewards", tags=["rewards"])


class ReferralResponse(BaseModel):
    referral_code: str
    referral_link: str
    referral_count: int
    earned_hours: int


class VPNConfigResponse(BaseModel):
    config: str
    expires_at: str
    hours_remaining: int
    reward_type: str


class UserStatsResponse(BaseModel):
    level: int
    experience: int
    xp_to_next_level: int
    streak_days: int
    vpn_hours_balance: int
    referral_count: int
    achievements_count: int
    stars_balance: int = 0


class AdminStarsRequest(BaseModel):
    target_telegram_id: int
    stars_amount: int


# Admin telegram IDs (can add stars to users)
ADMIN_IDS = [84481976]  # Add your telegram_id here


async def get_or_create_user(telegram_id: int, db: AsyncSession) -> User:
    """Получает или создаёт пользователя"""
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            referral_code=generate_referral_code(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


@router.post("/admin/add-stars")
async def admin_add_stars(
    request: AdminStarsRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to add stars to a user"""
    if user_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Find target user
    result = await db.execute(
        select(User).where(User.telegram_id == request.target_telegram_id)
    )
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add stars
    target_user.stars_balance += request.stars_amount
    await db.commit()
    
    logger.info(f"Admin {user_id} added {request.stars_amount} stars to user {request.target_telegram_id}")
    
    return {
        "success": True,
        "target_telegram_id": request.target_telegram_id,
        "stars_added": request.stars_amount,
        "new_balance": target_user.stars_balance
    }


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику пользователя"""
    user = await get_or_create_user(user_id, db)
    
    # Считаем достижения
    result = await db.execute(
        select(Achievement).where(Achievement.user_id == user.id)
    )
    achievements = result.scalars().all()
    
    # XP до следующего уровня
    from app.services.vpn_rewards import get_level_xp_required
    xp_needed = get_level_xp_required(user.level)
    
    return UserStatsResponse(
        level=user.level,
        experience=user.experience,
        xp_to_next_level=xp_needed - user.experience,
        streak_days=user.streak_days,
        vpn_hours_balance=user.vpn_hours_balance,
        referral_count=user.referral_count,
        achievements_count=len(achievements),
        stars_balance=user.stars_balance
    )


# === WEATHER & SHELTER SYSTEM ===

@router.get("/weather")
async def get_weather(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current weather and shelter status"""
    user = await get_or_create_user(user_id, db)
    shelter_level = getattr(user, 'shelter_level', 0) or 0
    
    weather = get_current_weather()
    shelter = get_shelter_info(shelter_level)
    effects = calculate_weather_effects(weather, shelter_level)
    hiding = should_pet_hide(weather, shelter_level)
    
    return {
        "weather": weather,
        "shelter": {
            "level": shelter_level,
            **shelter
        },
        "effects": effects,
        "pet_hiding": hiding,
        "next_upgrade": get_next_shelter_upgrade(shelter_level)
    }


@router.get("/shelter")
async def get_shelter_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get shelter info and available upgrades"""
    user = await get_or_create_user(user_id, db)
    shelter_level = getattr(user, 'shelter_level', 0) or 0
    
    current = get_shelter_info(shelter_level)
    next_upgrade = get_next_shelter_upgrade(shelter_level)
    all_levels = get_all_shelter_levels()
    
    return {
        "current_level": shelter_level,
        "current": current,
        "next_upgrade": next_upgrade,
        "all_levels": all_levels,
        "stars_balance": user.stars_balance
    }


@router.post("/shelter/upgrade")
async def upgrade_shelter(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade shelter to next level"""
    user = await get_or_create_user(user_id, db)
    shelter_level = getattr(user, 'shelter_level', 0) or 0
    
    next_upgrade = get_next_shelter_upgrade(shelter_level)
    if not next_upgrade:
        raise HTTPException(status_code=400, detail="Максимальный уровень укрытия!")
    
    price = next_upgrade["price"]
    if user.stars_balance < price:
        raise HTTPException(
            status_code=400, 
            detail=f"Не хватает звёзд! Нужно: {price}, есть: {user.stars_balance}"
        )
    
    # Upgrade!
    user.stars_balance -= price
    user.shelter_level = next_upgrade["level"]
    
    # Barrel progress
    user.barrel_progress = (user.barrel_progress or 0) + 1
    barrel_reward = None
    if user.barrel_progress >= 100:
        user.barrel_progress -= 100
        user.barrel_completions = (user.barrel_completions or 0) + 1
        user.vpn_hours_balance = (user.vpn_hours_balance or 0) + 720
        barrel_reward = {"filled": True, "reward": "720h VPN"}
    
    await db.commit()
    
    shelter = get_shelter_info(user.shelter_level)
    
    return {
        "success": True,
        "message": f"🎉 Улучшено до: {shelter['name']}!",
        "shelter": {
            "level": user.shelter_level,
            **shelter
        },
        "stars_spent": price,
        "new_balance": user.stars_balance,
        "next_upgrade": get_next_shelter_upgrade(user.shelter_level),
        "barrel_reward": barrel_reward
    }


# === STAR ROULETTE SYSTEM ===

from app.services.roulette import (
    RoulettePool, get_today_roulette_id, get_next_draw_time,
    get_current_twist, format_winner_notification, format_winner_share_text,
    ROULETTE_CONFIG
)


class RouletteBetRequest(BaseModel):
    bet_amount: int = Field(..., ge=10, le=500)


@router.get("/roulette")
async def get_roulette_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о текущей рулетке"""
    from app.services.notifications import send_roulette_result_notification
    from app.models.user import Transaction
    import asyncio
    
    user = await get_or_create_user(user_id, db)
    roulette_id = get_today_roulette_id()
    
    pool = RoulettePool.get_or_create(roulette_id)
    
    # === АВТОМАТИЧЕСКИЙ РОЗЫГРЫШ ===
    # Если время прошло, участников >= 2, и розыгрыш не проведён
    now = datetime.now(timezone.utc)
    draw_time_today = now.replace(
        hour=ROULETTE_CONFIG["draw_hour_utc"],
        minute=0, second=0, microsecond=0
    )
    
    if (not pool["drawn"] and 
        len(pool["participants"]) >= 2 and 
        now >= draw_time_today):
        
        logger.info(f"Auto-draw triggered for {roulette_id}")
        winners = RoulettePool.draw_winners(roulette_id)
        pool_total = pool["total"]
        
        # Выдаём призы победителям
        for winner in winners:
            try:
                result = await db.execute(
                    select(User).where(User.telegram_id == winner["user_id"])
                )
                winner_user = result.scalar_one_or_none()
                
                if winner_user:
                    winner_user.stars_balance += winner["prize"]
                    
                    # Записываем транзакцию
                    tx = Transaction(
                        user_id=winner_user.id,
                        currency="stars",
                        amount=winner["prize"],
                        balance_after=winner_user.stars_balance,
                        tx_type="roulette_win",
                        description=f"🎰 Выигрыш в рулетке #{winner['place']} место",
                        reference_id=roulette_id
                    )
                    db.add(tx)
                    
                    if winner.get("vpn_bonus", 0) > 0:
                        winner_user.vpn_hours_balance += winner["vpn_bonus"]
                    
                    asyncio.create_task(
                        send_roulette_result_notification(winner["user_id"], winner, pool_total)
                    )
                    logger.info(f"Auto-prize: {winner['user_id']} got {winner['prize']} stars")
            except Exception as e:
                logger.error(f"Auto-draw prize error: {e}")
        
        await db.commit()
        pool = RoulettePool.get_or_create(roulette_id)  # Reload
    
    pool_info = RoulettePool.get_pool_info(roulette_id)
    my_bet = RoulettePool.get_participant(roulette_id, user_id)
    
    return {
        **pool_info,
        "my_bet": my_bet["bet"] if my_bet else None,
        "my_stars": user.stars_balance,
        "min_bet": ROULETTE_CONFIG["min_bet"],
        "max_bet": ROULETTE_CONFIG["max_bet"],
        "can_bet": my_bet is None and not pool_info["is_drawn"]
    }


@router.post("/roulette/bet")
async def place_roulette_bet(
    request: RouletteBetRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Сделать ставку в рулетку"""
    from app.models.user import Transaction
    
    user = await get_or_create_user(user_id, db)
    roulette_id = get_today_roulette_id()
    
    # Проверки
    pool_info = RoulettePool.get_pool_info(roulette_id)
    if pool_info["is_drawn"]:
        raise HTTPException(status_code=400, detail="Розыгрыш уже прошёл! Ждите завтра.")
    
    existing = RoulettePool.get_participant(roulette_id, user_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Вы уже участвуете! Ваша ставка: {existing['bet']} ⭐")
    
    if user.stars_balance < request.bet_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Не хватает звёзд! Нужно: {request.bet_amount}, есть: {user.stars_balance}"
        )
    
    # Списываем звёзды
    user.stars_balance -= request.bet_amount
    
    # Записываем транзакцию
    tx = Transaction(
        user_id=user.id,
        currency="stars",
        amount=-request.bet_amount,
        balance_after=user.stars_balance,
        tx_type="roulette_bet",
        description=f"🎰 Ставка в рулетку",
        reference_id=roulette_id
    )
    db.add(tx)
    await db.commit()
    
    # Добавляем в пул
    username = user.username or f"user_{user_id}"
    RoulettePool.add_participant(roulette_id, user_id, username, request.bet_amount)
    
    new_pool_info = RoulettePool.get_pool_info(roulette_id)
    twist = get_current_twist(new_pool_info["total_pool"])
    
    logger.info(f"Roulette bet: user {user_id} bet {request.bet_amount} stars")
    
    return {
        "success": True,
        "message": f"🎰 Ставка принята: {request.bet_amount} ⭐",
        "bet": request.bet_amount,
        "new_balance": user.stars_balance,
        "pool_total": new_pool_info["total_pool"],
        "participants": new_pool_info["participants_count"],
        "current_twist": twist,
        "next_draw": new_pool_info["next_draw"]
    }


@router.post("/roulette/draw")
async def draw_roulette(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Провести розыгрыш (только админ)"""
    from app.services.notifications import send_roulette_result_notification
    import asyncio
    
    if user_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Только админ может проводить розыгрыш")
    
    roulette_id = get_today_roulette_id()
    pool = RoulettePool.get_or_create(roulette_id)
    
    if pool["drawn"]:
        return {
            "success": False,
            "message": "Розыгрыш уже проведён",
            "winners": pool["winners"]
        }
    
    if len(pool["participants"]) < 2:
        return {
            "success": False,
            "message": "Недостаточно участников (минимум 2)"
        }
    
    winners = RoulettePool.draw_winners(roulette_id)
    pool_total = pool["total"]
    
    # АВТОМАТИЧЕСКАЯ ВЫДАЧА ПРИЗОВ ПОБЕДИТЕЛЯМ
    prizes_distributed = []
    for winner in winners:
        try:
            # Находим пользователя в БД
            result = await db.execute(
                select(User).where(User.telegram_id == winner["user_id"])
            )
            winner_user = result.scalar_one_or_none()
            
            if winner_user:
                # Начисляем звёзды
                winner_user.stars_balance += winner["prize"]
                
                # Начисляем VPN бонус если есть
                if winner.get("vpn_bonus", 0) > 0:
                    winner_user.vpn_hours_balance += winner["vpn_bonus"]
                
                prizes_distributed.append({
                    "user_id": winner["user_id"],
                    "stars": winner["prize"],
                    "vpn_hours": winner.get("vpn_bonus", 0)
                })
                
                # Отправляем уведомление победителю
                asyncio.create_task(
                    send_roulette_result_notification(winner["user_id"], winner, pool_total)
                )
                
                logger.info(f"Prize distributed to {winner['user_id']}: {winner['prize']} stars")
        except Exception as e:
            logger.error(f"Failed to distribute prize to {winner['user_id']}: {e}")
    
    await db.commit()
    
    # Форматируем уведомление для админа
    notification = format_winner_notification(winners, pool_total, roulette_id)
    
    logger.info(f"Roulette drawn: {roulette_id}, winners: {winners}, prizes auto-distributed: {prizes_distributed}")
    
    return {
        "success": True,
        "message": "🎉 Розыгрыш проведён! Призы автоматически начислены!",
        "roulette_id": roulette_id,
        "pool_total": pool_total,
        "participants_count": len(pool["participants"]),
        "winners": winners,
        "prizes_distributed": prizes_distributed,
        "admin_notification": notification,
        "share_texts": [
            format_winner_share_text(w, pool_total)
            for w in winners
        ]
    }


@router.get("/roulette/history")
async def get_roulette_history(
    user_id: int = Depends(get_current_user_id)
):
    """История розыгрышей (за последние дни)"""
    # Пока возвращаем текущий розыгрыш (для MVP)
    roulette_id = get_today_roulette_id()
    pool = RoulettePool.get_or_create(roulette_id)
    
    return {
        "today": {
            "roulette_id": roulette_id,
            "pool_total": pool["total"],
            "participants": len(pool["participants"]),
            "drawn": pool["drawn"],
            "winners": pool["winners"] if pool["drawn"] else []
        }
    }


# === ИСТОРИЯ ТРАНЗАКЦИЙ ===
@router.get("/transactions")
async def get_transaction_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    currency: str = "all",  # all, stars, tokens
    limit: int = 50
):
    """Получить историю транзакций пользователя"""
    from app.models.user import Transaction
    
    user = await get_or_create_user(user_id, db)
    
    query = select(Transaction).where(Transaction.user_id == user.id)
    
    if currency != "all":
        query = query.where(Transaction.currency == currency)
    
    query = query.order_by(Transaction.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Группируем по дате
    tx_list = []
    for tx in transactions:
        tx_list.append({
            "id": tx.id,
            "currency": tx.currency,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "type": tx.tx_type,
            "description": tx.description,
            "reference_id": tx.reference_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "is_income": tx.amount > 0
        })
    
    # Статистика
    total_income = sum(tx["amount"] for tx in tx_list if tx["amount"] > 0)
    total_spent = abs(sum(tx["amount"] for tx in tx_list if tx["amount"] < 0))
    
    return {
        "transactions": tx_list,
        "stats": {
            "total_income": total_income,
            "total_spent": total_spent,
            "net": total_income - total_spent,
            "count": len(tx_list)
        },
        "current_balance": {
            "stars": user.stars_balance,
            "tokens": user.token_balance
        }
    }


@router.get("/progression")
async def get_progression_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить полную информацию о прогрессии питомца"""
    from app.services.progression import (
        get_evolution_for_level,
        get_next_evolution,
        get_evolutions_for_pet,
        get_level_reward,
        LEVEL_REWARDS
    )
    from app.services.vpn_rewards import get_level_xp_required
    
    user = await get_or_create_user(user_id, db)
    pet_type = user.pet_type or "kitty"  # Default to kitty
    
    current_evo = get_evolution_for_level(user.level, pet_type)
    next_evo = get_next_evolution(user.level, pet_type)
    xp_needed = get_level_xp_required(user.level)
    
    # Get evolutions for this pet type
    pet_evolutions = get_evolutions_for_pet(pet_type)
    
    # Список всех эволюций с прогрессом
    evolutions = []
    for evo_level, evo_data in sorted(pet_evolutions.items()):
        evolutions.append({
            "level": evo_level,
            "name": evo_data["name"],
            "emoji": evo_data["emoji"],
            "description": evo_data["description"],
            "unlocked": user.level >= evo_level,
            "current": current_evo and current_evo["level"] == evo_level
        })
    
    # Награды за уровни
    level_rewards = []
    for lvl, reward in sorted(LEVEL_REWARDS.items()):
        level_rewards.append({
            "level": lvl,
            "vpn_hours": reward["vpn_hours"],
            "title": reward["title"],
            "claimed": user.level >= lvl  # TODO: отслеживать claimed отдельно
        })
    
    return {
        "user": {
            "level": user.level,
            "experience": user.experience,
            "xp_to_next": xp_needed - user.experience,
            "xp_progress_percent": round((user.experience / xp_needed) * 100, 1) if xp_needed > 0 else 100,
            "total_purchases": user.total_purchases,
            "vpn_hours": user.vpn_hours_balance
        },
        "current_evolution": current_evo,
        "next_evolution": next_evo,
        "levels_to_next_evo": next_evo["level"] - user.level if next_evo else 0,
        "evolutions": evolutions,
        "level_rewards": level_rewards,
        "bonuses": current_evo.get("bonus", {}) if current_evo else {}
    }


@router.get("/referral", response_model=ReferralResponse)
async def get_referral_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить реферальную ссылку"""
    user = await get_or_create_user(user_id, db)
    
    # Генерируем код если нет
    if not user.referral_code:
        user.referral_code = generate_referral_code()
        await db.commit()
    
    bot_username = "tama_guardian_bot"  # Из настроек
    referral_link = f"https://t.me/{bot_username}?start=ref_{user.referral_code}"
    
    return ReferralResponse(
        referral_code=user.referral_code,
        referral_link=referral_link,
        referral_count=user.referral_count,
        earned_hours=user.referral_count * REWARDS["referral"]
    )


@router.post("/referral/apply")
async def apply_referral(
    referral_code: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Применить реферальный код"""
    user = await get_or_create_user(user_id, db)
    
    # Проверяем что пользователь ещё не использовал реферал
    if user.referred_by_id:
        raise HTTPException(status_code=400, detail="Реферальный код уже использован")
    
    # Ищем владельца кода
    result = await db.execute(
        select(User).where(User.referral_code == referral_code.upper())
    )
    referrer = result.scalar_one_or_none()
    
    if not referrer:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")
    
    if referrer.id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя использовать свой код")
    
    # Применяем реферал
    user.referred_by_id = referrer.id
    referrer.referral_count += 1
    referrer.vpn_hours_balance += REWARDS["referral"]
    
    # Награда новому пользователю тоже
    user.vpn_hours_balance += 24  # 1 день новичку
    
    await db.commit()
    
    return {
        "message": "Реферальный код применён!",
        "bonus_hours": 24,
        "referrer_bonus_hours": REWARDS["referral"]
    }


@router.post("/vpn/generate", response_model=VPNConfigResponse)
async def generate_vpn_config(
    hours: int = 24,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Сгенерировать VPN конфиг из баланса"""
    user = await get_or_create_user(user_id, db)
    
    if user.vpn_hours_balance < hours:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно часов. Баланс: {user.vpn_hours_balance}h, запрошено: {hours}h"
        )
    
    # Генерируем конфиг
    config_data = await generate_amnezia_config(user_id, hours)
    if not config_data:
        raise HTTPException(status_code=500, detail="Ошибка генерации конфига")
    
    # Списываем часы
    user.vpn_hours_balance -= hours
    
    # Сохраняем конфиг
    expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    vpn_config = VPNConfig(
        user_id=user.id,
        config_data=config_data,
        config_type="amnezia-xray",
        expires_at=expires_at,
        reward_type="balance",
        reward_description=f"Списано {hours}h с баланса"
    )
    db.add(vpn_config)
    await db.commit()
    
    return VPNConfigResponse(
        config=config_data,
        expires_at=expires_at.isoformat(),
        hours_remaining=user.vpn_hours_balance,
        reward_type="balance"
    )


@router.get("/vpn/active")
async def get_active_vpn_configs(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить активные VPN конфиги"""
    user = await get_or_create_user(user_id, db)
    
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(VPNConfig)
        .where(VPNConfig.user_id == user.id)
        .where(VPNConfig.expires_at > now)
        .where(VPNConfig.is_active == True)
    )
    configs = result.scalars().all()
    
    return {
        "active_configs": [
            {
                "id": c.id,
                "config": c.config_data,
                "expires_at": c.expires_at.isoformat(),
                "hours_left": int((c.expires_at - now).total_seconds() / 3600),
                "reward_type": c.reward_type
            }
            for c in configs
        ],
        "balance_hours": user.vpn_hours_balance
    }


@router.get("/achievements")
async def get_achievements(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить список достижений"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(Achievement).where(Achievement.user_id == user.id)
    )
    user_achievements = {a.achievement_type: a for a in result.scalars().all()}
    
    achievements_list = []
    for key, data in ACHIEVEMENTS.items():
        unlocked = key in user_achievements
        claimed = user_achievements[key].reward_claimed if unlocked else False
        
        achievements_list.append({
            "id": key,
            "name": data["name"],
            "reward_hours": data["reward_hours"],
            "unlocked": unlocked,
            "reward_claimed": claimed,
            "unlocked_at": user_achievements[key].unlocked_at.isoformat() if unlocked else None
        })
    
    return {"achievements": achievements_list}


@router.post("/achievements/{achievement_id}/claim")
async def claim_achievement_reward(
    achievement_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить награду за достижение"""
    user = await get_or_create_user(user_id, db)
    
    if achievement_id not in ACHIEVEMENTS:
        raise HTTPException(status_code=404, detail="Достижение не найдено")
    
    result = await db.execute(
        select(Achievement)
        .where(Achievement.user_id == user.id)
        .where(Achievement.achievement_type == achievement_id)
    )
    achievement = result.scalar_one_or_none()
    
    if not achievement:
        raise HTTPException(status_code=400, detail="Достижение не разблокировано")
    
    if achievement.reward_claimed:
        raise HTTPException(status_code=400, detail="Награда уже получена")
    
    # Выдаём награду
    reward_hours = ACHIEVEMENTS[achievement_id]["reward_hours"]
    user.vpn_hours_balance += reward_hours
    achievement.reward_claimed = True
    
    await db.commit()
    
    return {
        "message": f"Награда получена: +{reward_hours}h VPN!",
        "new_balance": user.vpn_hours_balance
    }


class AddVPNHoursRequest(BaseModel):
    user_id: int = Field(gt=0)
    hours: int = Field(gt=0, le=24 * 365)
    reason: str = Field(min_length=3, max_length=128)


@router.post("/add-vpn-hours")
async def add_vpn_hours(
    request: AddVPNHoursRequest,
    _: None = Depends(require_internal_api_token),
    db: AsyncSession = Depends(get_db)
):
    """Добавить VPN часы (для внутреннего использования, например после покупки)"""
    user = await get_or_create_user(request.user_id, db)
    
    user.vpn_hours_balance += request.hours
    await db.commit()
    
    logger.info(f"Added {request.hours}h VPN to user {request.user_id}, reason: {request.reason}")
    
    return {
        "success": True,
        "hours_added": request.hours,
        "new_balance": user.vpn_hours_balance,
        "reason": request.reason
    }


# === LANGUAGE SETTINGS ===

@router.get("/languages")
async def get_languages():
    """Get list of available languages"""
    return {"languages": get_available_languages()}


@router.get("/language")
async def get_user_language(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's current language"""
    user = await get_or_create_user(user_id, db)
    return {
        "language": user.language,
        "available": get_available_languages()
    }


class SetLanguageRequest(BaseModel):
    language: str


@router.post("/language")
async def set_user_language(
    request: SetLanguageRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Set user's preferred language"""
    available = [l["code"] for l in get_available_languages()]
    if request.language not in available:
        raise HTTPException(status_code=400, detail=f"Language not available. Available: {available}")
    
    user = await get_or_create_user(user_id, db)
    user.language = request.language
    await db.commit()
    
    return {
        "success": True,
        "language": request.language,
        "message": get_text("welcome_title", request.language)
    }


@router.get("/texts")
async def get_translations(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all translations for user's language"""
    user = await get_or_create_user(user_id, db)
    lang = user.language
    
    # Return all essential UI texts as flat object for easy JS access
    return {
        "language": lang,
        # Action buttons
        "feed_btn": get_text("action_feed", lang),
        "play_btn": get_text("action_play", lang),
        "sleep_btn": get_text("sleep_btn", lang),
        "wake_btn": get_text("wake_btn", lang),
        "bath_btn": get_text("action_bath", lang),
        "train_btn": get_text("action_train", lang),
        "heal_btn": get_text("action_heal", lang),
        "light_on_btn": get_text("light_on_btn", lang),
        "light_off_btn": get_text("light_off_btn", lang),
        
        # Navigation
        "nav_home": get_text("nav_home", lang),
        "nav_grow": get_text("nav_grow", lang),
        "nav_style": get_text("nav_style", lang),
        "nav_shop": get_text("nav_shop", lang),
        "nav_top": get_text("nav_top", lang),
        "nav_menu": get_text("nav_menu", lang),
        
        # Modal titles
        "shop_title": get_text("shop_title", lang),
        "wardrobe_title": get_text("wardrobe_title", lang),
        "settings_title": get_text("settings_title", lang),
        "leaderboard_title": get_text("leaderboard_title", lang),
        
        # Status messages
        "pet_hungry": get_text("pet_hungry", lang),
        "pet_tired": get_text("pet_tired", lang),
        "pet_sad": get_text("pet_sad", lang),
        "pet_happy": get_text("pet_happy", lang),
        "pet_fine": get_text("pet_fine", lang),
        "pet_sick": get_text("pet_sick", lang),
        "pet_sleeping": get_text("pet_sleeping", lang),
        "pet_dirty": get_text("pet_dirty", lang),
        
        # Stats
        "stat_hunger": get_text("stat_hunger", lang),
        "stat_energy": get_text("stat_energy", lang),
        "stat_happiness": get_text("stat_happiness", lang),
        "stat_hygiene": get_text("stat_hygiene", lang),
        "stat_health": get_text("stat_health", lang),
        
        # Other
        "barrel_title": get_text("barrel_title", lang),
        "barrel_reward": get_text("barrel_reward", lang),
        "barrel_purchases": get_text("barrel_purchases", lang),
        "support_title": get_text("support_title", lang),
        "support_text": get_text("support_text", lang),
        
        # Wardrobe
        "equipped": get_text("equipped", lang),
        "inventory": get_text("inventory", lang),
        "no_items": get_text("no_items", lang),
        "buy_in_shop": get_text("buy_in_shop", lang),
        "all_equipped": get_text("all_equipped", lang),
        
        # Market
        "market_title": get_text("market_title", lang),
        "market_p2p": get_text("market_p2p", lang),
        "market_desc": get_text("market_desc", lang),
        "commission": get_text("commission", lang),
        "sell_item": get_text("sell_item", lang),
        "sell_title": get_text("sell_title", lang),
        "select_item": get_text("select_item", lang),
        "set_price": get_text("set_price", lang),
        "you_receive": get_text("you_receive", lang),
        "after_fee": get_text("after_fee", lang),
        "list_for_sale": get_text("list_for_sale", lang),
        "my_listings": get_text("my_listings", lang),
        "no_listings": get_text("no_listings", lang),
        "be_first": get_text("be_first", lang),
        "cancel": get_text("cancel", lang),
        "buy": get_text("buy", lang),
        
        # Stars
        "buy_stars": get_text("buy_stars", lang),
        "your_balance": get_text("your_balance", lang),
        "stars": get_text("stars", lang),
        "tap_to_buy": get_text("tap_to_buy", lang),
        
        # Loading
        "loading": get_text("loading", lang),
        
        # Invite
        "invite_title": get_text("invite_title", lang),
        "invite_reward": get_text("invite_reward", lang),
        "invited": get_text("invited", lang),
        "per_friend": get_text("per_friend", lang),
        "share_link": get_text("share_link", lang),
        "your_code": get_text("your_code", lang),
        
        # Change Pet
        "change_pet": get_text("change_pet", lang),
        "select_new_pet": get_text("select_new_pet", lang),
        "progress_saved": get_text("progress_saved", lang),
    }


# === SUPPORT ===

class SupportRequest(BaseModel):
    message: str
    category: str = "general"  # general, payment, bug, feature


@router.post("/support")
async def send_support_request(
    request: SupportRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Send support request"""
    user = await get_or_create_user(user_id, db)
    
    # Check cooldown (1 message per 5 minutes)
    if user.last_support_request:
        cooldown = datetime.now(timezone.utc) - user.last_support_request
        if cooldown.total_seconds() < 300:  # 5 minutes
            remaining = 300 - int(cooldown.total_seconds())
            raise HTTPException(
                status_code=429, 
                detail=f"Please wait {remaining} seconds before sending another request"
            )
    
    # Log support request (in production: send to admin/database)
    logger.info(f"SUPPORT REQUEST from user {user_id}: [{request.category}] {request.message}")
    
    user.last_support_request = datetime.now(timezone.utc)
    await db.commit()
    
    lang = user.language
    return {
        "success": True,
        "message": get_text("support_text", lang),
        "ticket_id": f"SUP-{user.id}-{int(datetime.now().timestamp())}"
    }


@router.get("/faq")
async def get_faq(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get FAQ in user's language"""
    user = await get_or_create_user(user_id, db)
    lang = user.language
    
    faq = [
        {"q": get_text("faq_q1", lang), "a": get_text("faq_a1", lang)},
        {"q": get_text("faq_q2", lang), "a": get_text("faq_a2", lang)},
        {"q": get_text("faq_q3", lang), "a": get_text("faq_a3", lang)},
        {"q": get_text("faq_q4", lang), "a": get_text("faq_a4", lang)},
        {"q": get_text("faq_q5", lang), "a": get_text("faq_a5", lang)},
    ]
    
    return {"faq": faq, "language": lang}


# === PET SELECTION ===

@router.get("/pets")
async def get_all_pets(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all available pets (free and premium)"""
    user = await get_or_create_user(user_id, db)
    
    # Parse owned pets
    owned_pets = set()
    if user.owned_pets:
        owned_pets = set(user.owned_pets.split(","))
    
    # All free pets are owned by default
    for pet in FREE_PETS:
        owned_pets.add(pet["id"])
    
    free_pets = []
    for pet in get_free_pets():
        free_pets.append({
            **pet,
            "owned": True,
            "selected": user.pet_type == pet["id"]
        })
    
    premium_pets = []
    for pet in get_premium_pets():
        premium_pets.append({
            **pet,
            "owned": pet["id"] in owned_pets,
            "selected": user.pet_type == pet["id"]
        })
    
    return {
        "free_pets": free_pets,
        "premium_pets": premium_pets,
        "selected_pet": user.pet_type,
        "stars_balance": user.stars_balance,
        "needs_selection": user.pet_type is None
    }


@router.get("/pet/selected")
async def get_selected_pet(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's currently selected pet"""
    user = await get_or_create_user(user_id, db)
    
    if not user.pet_type:
        return {
            "selected": False,
            "pet": None,
            "needs_selection": True
        }
    
    pet = get_pet_by_id(user.pet_type)
    return {
        "selected": True,
        "pet": pet,
        "needs_selection": False
    }


class SelectPetRequest(BaseModel):
    pet_id: str


@router.post("/pet/select")
async def select_pet(
    request: SelectPetRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Select a pet (free) or buy and select (premium)"""
    user = await get_or_create_user(user_id, db)
    
    pet = get_pet_by_id(request.pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    # Parse owned pets
    owned_pets = set()
    if user.owned_pets:
        owned_pets = set(user.owned_pets.split(","))
    
    # Free pets are always available
    if is_pet_free(request.pet_id):
        user.pet_type = request.pet_id
        user.pet_selected_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "success": True,
            "message": f"{pet['name']} selected!",
            "pet": pet,
            "purchased": False
        }
    
    # Premium pet - check if already owned
    if request.pet_id in owned_pets:
        user.pet_type = request.pet_id
        user.pet_selected_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "success": True,
            "message": f"{pet['name']} selected!",
            "pet": pet,
            "purchased": False
        }
    
    # Need to buy - check stars balance
    price = get_pet_price(request.pet_id)
    if user.stars_balance < price:
        return {
            "success": False,
            "message": f"Not enough stars! Need {price}, have {user.stars_balance}",
            "price": price,
            "balance": user.stars_balance,
            "need_purchase": True
        }
    
    # Purchase the pet
    user.stars_balance -= price
    owned_pets.add(request.pet_id)
    user.owned_pets = ",".join(owned_pets)
    user.pet_type = request.pet_id
    user.pet_selected_at = datetime.now(timezone.utc)
    
    # Count towards barrel
    user.total_purchases += 1
    user.barrel_progress += 1
    
    barrel_reward = None
    if user.barrel_progress >= 100:
        user.barrel_progress -= 100
        user.barrel_completions += 1
        user.vpn_hours_balance += 720
        barrel_reward = {"filled": True, "reward": "720h VPN"}
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"{pet['name']} purchased and selected!",
        "pet": pet,
        "purchased": True,
        "stars_spent": price,
        "new_balance": user.stars_balance,
        "barrel": barrel_reward
    }


# === TELEGRAM STARS ===

@router.get("/stars/balance")
async def get_stars_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's Telegram Stars balance"""
    user = await get_or_create_user(user_id, db)
    return {
        "balance": user.stars_balance,
        "total_purchases": user.total_purchases
    }


@router.get("/stars/packages")
async def get_stars_packages():
    """Get available stars packages for purchase"""
    return {
        "packages": [
            {"id": "stars_50", "stars": 50, "price_stars": 50, "bonus": 0, "label": "50 ⭐"},
            {"id": "stars_100", "stars": 110, "price_stars": 100, "bonus": 10, "label": "100+10 ⭐"},
            {"id": "stars_250", "stars": 280, "price_stars": 250, "bonus": 30, "label": "250+30 ⭐"},
            {"id": "stars_500", "stars": 600, "price_stars": 500, "bonus": 100, "label": "500+100 ⭐"},
            {"id": "stars_1000", "stars": 1250, "price_stars": 1000, "bonus": 250, "label": "1000+250 ⭐"},
        ],
        "note": "Payment via Telegram Stars. Bonus stars included!"
    }


class AddStarsRequest(BaseModel):
    user_id: int = Field(gt=0)
    amount: int = Field(gt=0)
    telegram_payment_id: str = Field(min_length=1, max_length=255)


class CreateInvoiceRequest(BaseModel):
    package_id: str


@router.post("/stars/create-invoice")
async def create_stars_invoice(
    request: CreateInvoiceRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Create invoice link for Telegram Stars payment"""
    import httpx
    from app.settings import settings
    
    logger.info(f"Creating invoice for user {user_id}, package: {request.package_id}")
    
    packages = {
        "stars_50": {"stars": 50, "price": 50, "bonus": 0, "label": "50 \u2b50 \u043c\u043e\u043d\u0435\u0442"},
        "stars_100": {"stars": 110, "price": 100, "bonus": 10, "label": "110 \u2b50 \u043c\u043e\u043d\u0435\u0442 (+10%)"},
        "stars_250": {"stars": 280, "price": 250, "bonus": 30, "label": "280 \u2b50 \u043c\u043e\u043d\u0435\u0442 (+12%)"},
        "stars_500": {"stars": 600, "price": 500, "bonus": 100, "label": "600 \u2b50 \u043c\u043e\u043d\u0435\u0442 (+20%)"},
        "stars_1000": {"stars": 1250, "price": 1000, "bonus": 250, "label": "1250 \u2b50 \u043c\u043e\u043d\u0435\u0442 (+25%)"},
    }
    
    pkg = packages.get(request.package_id)
    if not pkg:
        logger.error(f"Invalid package: {request.package_id}")
        raise HTTPException(status_code=400, detail="Invalid package")
    
    # Create invoice via Telegram Bot API
    bot_token = settings.bot_token
    logger.info(f"Using bot_token: {bot_token[:10]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "title": pkg["label"],
                "description": f"\u041f\u043e\u043a\u0443\u043f\u043a\u0430 {pkg['stars']} \u0438\u0433\u0440\u043e\u0432\u044b\u0445 \u043c\u043e\u043d\u0435\u0442",
                "payload": f"{request.package_id}_{user_id}",
                "currency": "XTR",
                "prices": [{"label": "Stars", "amount": pkg["price"]}]
            }
            logger.info(f"Telegram API request: {payload}")
            
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/createInvoiceLink",
                json=payload
            )
            data = response.json()
            logger.info(f"Telegram API response: {data}")
            
            if data.get("ok"):
                return {"invoice_link": data["result"]}
            else:
                error_msg = data.get("description", "Failed to create invoice")
                logger.error(f"Telegram API error: {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.exception(f"Invoice creation exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stars/add")
async def add_stars(
    request: AddStarsRequest,
    _: None = Depends(require_internal_api_token),
    db: AsyncSession = Depends(get_db)
):
    """Add stars to user balance (internal endpoint, idempotent by payment ID)"""
    # Check for duplicate payment (idempotency)
    from app.models.shop import StarTransaction
    existing_payment = await db.execute(
        select(StarTransaction).where(
            StarTransaction.telegram_payment_id == request.telegram_payment_id
        )
    )
    existing_tx = existing_payment.scalar_one_or_none()
    if existing_tx:
        user_result = await db.execute(select(User).where(User.id == existing_tx.user_id))
        existing_user = user_result.scalar_one_or_none()
        return {
            "success": True,
            "already_processed": True,
            "stars_added": 0,
            "new_balance": existing_user.stars_balance if existing_user else 0,
        }

    user = await get_or_create_user(request.user_id, db)
    
    # Calculate bonus based on amount
    bonus = 0
    if request.amount >= 1000:
        bonus = int(request.amount * 0.25)
    elif request.amount >= 500:
        bonus = int(request.amount * 0.20)
    elif request.amount >= 250:
        bonus = int(request.amount * 0.12)
    elif request.amount >= 100:
        bonus = int(request.amount * 0.10)
    
    total = request.amount + bonus
    user.stars_balance += total
    
    # Record transaction
    transaction = StarTransaction(
        user_id=user.id,
        telegram_payment_id=request.telegram_payment_id,
        stars_amount=total,
        purchase_type="stars_pack",
        purchase_description=f"Telegram Stars top-up {request.amount} (+{bonus})",
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(transaction)
    await db.commit()
    
    logger.info(
        "User %s bought %s stars (+%s bonus) = %s",
        request.user_id,
        request.amount,
        bonus,
        total
    )
    
    return {
        "success": True,
        "stars_added": total,
        "base": request.amount,
        "bonus": bonus,
        "new_balance": user.stars_balance
    }


# === LEADERBOARDS ===

@router.get("/leaderboard/{board_type}")
async def get_leaderboard(
    board_type: str,
    limit: int = 50,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get leaderboard by type: level, xp, streak, vpn, purchases"""
    current_user = await get_or_create_user(user_id, db)
    
    # Define ordering based on board type
    order_column = {
        "level": User.level.desc(),
        "xp": User.experience.desc(),
        "streak": User.streak_days.desc(),
        "vpn": User.vpn_hours_balance.desc(),
        "purchases": User.total_purchases.desc(),
    }.get(board_type)
    
    if not order_column:
        raise HTTPException(status_code=400, detail="Invalid board type. Use: level, xp, streak, vpn, purchases")
    
    # Get top users
    result = await db.execute(
        select(User)
        .order_by(order_column)
        .limit(limit)
    )
    users = result.scalars().all()
    
    # Build leaderboard
    leaderboard = []
    for rank, user in enumerate(users, 1):
        # Get user's pet info
        from app.services.pet_types import get_pet_by_id, FREE_PETS
        pet = get_pet_by_id(user.pet_type) if user.pet_type else FREE_PETS[0]
        
        leaderboard.append({
            "rank": rank,
            "user_id": user.telegram_id,
            "username": user.username or f"User{user.telegram_id % 10000}",
            "first_name": user.first_name,
            "pet_emoji": pet["emoji"],
            "pet_name": pet["name"],
            "level": user.level,
            "experience": user.experience,
            "streak_days": user.streak_days,
            "vpn_hours": user.vpn_hours_balance,
            "total_purchases": user.total_purchases,
            "is_current_user": user.telegram_id == user_id
        })
    
    # Find current user's rank if not in top
    current_user_rank = None
    current_user_in_list = any(u["is_current_user"] for u in leaderboard)
    
    if not current_user_in_list:
        # Count users above current user
        count_query = {
            "level": select(User).where(User.level > current_user.level),
            "xp": select(User).where(User.experience > current_user.experience),
            "streak": select(User).where(User.streak_days > current_user.streak_days),
            "vpn": select(User).where(User.vpn_hours_balance > current_user.vpn_hours_balance),
            "purchases": select(User).where(User.total_purchases > current_user.total_purchases),
        }.get(board_type)
        
        result = await db.execute(count_query)
        users_above = len(result.scalars().all())
        current_user_rank = users_above + 1
        
        pet = get_pet_by_id(current_user.pet_type) if current_user.pet_type else FREE_PETS[0]
    
    return {
        "board_type": board_type,
        "leaderboard": leaderboard,
        "current_user": {
            "rank": current_user_rank,
            "level": current_user.level,
            "experience": current_user.experience,
            "streak_days": current_user.streak_days,
            "vpn_hours": current_user.vpn_hours_balance,
            "total_purchases": current_user.total_purchases,
            "in_top": current_user_in_list
        } if not current_user_in_list else None,
        "board_titles": {
            "level": "🏆 Top Level",
            "xp": "⭐ Top XP",
            "streak": "🔥 Top Streak",
            "vpn": "🛡️ Top VPN",
            "purchases": "💰 Top Buyers"
        }
    }


@router.get("/leaderboard-summary")
async def get_leaderboard_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of all leaderboards with top 3 for each"""
    current_user = await get_or_create_user(user_id, db)
    from app.services.pet_types import get_pet_by_id, FREE_PETS
    
    boards = []
    board_configs = [
        ("level", "🏆 Уровень", User.level.desc()),
        ("xp", "⭐ Опыт", User.experience.desc()),
        ("streak", "🔥 Стрик", User.streak_days.desc()),
    ]
    
    for board_id, title, order_col in board_configs:
        result = await db.execute(
            select(User).order_by(order_col).limit(3)
        )
        top_users = result.scalars().all()
        
        top3 = []
        for rank, user in enumerate(top_users, 1):
            pet = get_pet_by_id(user.pet_type) if user.pet_type else FREE_PETS[0]
            value = {
                "level": user.level,
                "xp": user.experience,
                "streak": user.streak_days,
            }.get(board_id, 0)
            
            top3.append({
                "rank": rank,
                "pet_emoji": pet["emoji"],
                "username": user.username or user.first_name or f"Pet{user.id}",
                "value": value,
                "is_me": user.telegram_id == user_id
            })
        
        boards.append({
            "id": board_id,
            "title": title,
            "top3": top3
        })
    
    return {"boards": boards}
