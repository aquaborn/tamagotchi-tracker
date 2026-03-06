from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.deps.auth import get_current_user_id
from app.deps.db import get_db
from packages.core.core.domain.pet import apply_tick, PetState, clamp
from packages.core.core.repo.pet_repo import PetRepo
from app.models.user import User, Achievement
from app.services.vpn_rewards import (
    XP_REWARDS, 
    REWARDS,
    calculate_new_level, 
    check_streak,
    generate_referral_code
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/pet", tags=["pet"])


class ActionRequest(BaseModel):
    action: str


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


async def check_and_unlock_achievement(user: User, achievement_type: str, db: AsyncSession) -> bool:
    """Проверяет и разблокирует достижение"""
    result = await db.execute(
        select(Achievement)
        .where(Achievement.user_id == user.id)
        .where(Achievement.achievement_type == achievement_type)
    )
    existing = result.scalar_one_or_none()
    
    if not existing:
        achievement = Achievement(
            user_id=user.id,
            achievement_type=achievement_type
        )
        db.add(achievement)
        return True
    return False


async def process_action_rewards(user: User, action: str, pet_state: PetState, db: AsyncSession) -> dict:
    """Обрабатывает награды за действие с учётом бонусов от одежды"""
    from app.routers.shop import get_equipped_bonuses, get_active_boosts_list
    
    rewards = {
        "xp_gained": 0,
        "leveled_up": False,
        "new_level": user.level,
        "achievements_unlocked": [],
        "vpn_hours_earned": 0,
        "streak_updated": False,
        "bonuses_applied": []
    }
    
    now = datetime.now(timezone.utc)
    
    # Получаем бонусы от экипированных предметов
    equipped_bonuses = await get_equipped_bonuses(user.id, db)
    active_boosts = await get_active_boosts_list(user.id, db)
    
    # Рассчитываем множитель XP
    xp_multiplier = 1.0
    
    # Бонусы от одежды (xp_bonus_percent, angel_wings, etc)
    if "xp_bonus_percent" in equipped_bonuses:
        xp_multiplier += equipped_bonuses["xp_bonus_percent"] / 100
        rewards["bonuses_applied"].append(f"+{equipped_bonuses['xp_bonus_percent']}% XP from clothing")
    if "angel_wings" in equipped_bonuses:
        xp_multiplier += equipped_bonuses["angel_wings"] / 100
        rewards["bonuses_applied"].append(f"+{equipped_bonuses['angel_wings']}% XP from wings")
    if "dragon_wings" in equipped_bonuses:
        xp_multiplier += equipped_bonuses["dragon_wings"] / 100
        rewards["bonuses_applied"].append(f"+{equipped_bonuses['dragon_wings']}% XP from dragon wings")
    if "platinum_collar" in equipped_bonuses:
        xp_multiplier += 0.10  # +10% XP from platinum collar
        rewards["bonuses_applied"].append("+10% XP from platinum collar")
    
    # Бонусы от активных бустов
    for boost in active_boosts:
        if boost["effect_type"] == "xp_multiplier":
            xp_multiplier *= boost["effect_value"]
            rewards["bonuses_applied"].append(f"x{boost['effect_value']} XP boost")
    
    # Добавляем XP с учётом множителя
    base_xp = XP_REWARDS.get(action, 0)
    xp_reward = int(base_xp * xp_multiplier)
    
    if xp_reward > 0:
        new_xp, new_level, leveled_up = calculate_new_level(
            user.experience, xp_reward, user.level
        )
        user.experience = new_xp
        
        if leveled_up:
            old_level = user.level
            user.level = new_level
            rewards["leveled_up"] = True
            rewards["new_level"] = new_level
            
            # Награда за уровень
            user.vpn_hours_balance += REWARDS["level_up"]
            rewards["vpn_hours_earned"] += REWARDS["level_up"]
            
            # Достижения за уровни
            for level_milestone in [5, 10, 25]:
                if old_level < level_milestone <= new_level:
                    if await check_and_unlock_achievement(user, f"level_{level_milestone}", db):
                        rewards["achievements_unlocked"].append(f"level_{level_milestone}")
        
        rewards["xp_gained"] = xp_reward
    
    # Проверяем первые действия
    first_action_map = {
        "feed": "first_feed",
        "play": "first_play",
        "sleep": "first_sleep"
    }
    if action in first_action_map:
        if await check_and_unlock_achievement(user, first_action_map[action], db):
            rewards["achievements_unlocked"].append(first_action_map[action])
    
    # Проверяем стрик
    streak_result, should_increment = check_streak(user.last_activity_date, now)
    if streak_result != -1:
        user.streak_days = streak_result
    elif should_increment:
        user.streak_days += 1
        rewards["streak_updated"] = True
        
        # Достижения за стрик
        for streak_milestone in [3, 7, 30]:
            if user.streak_days == streak_milestone:
                if await check_and_unlock_achievement(user, f"streak_{streak_milestone}", db):
                    rewards["achievements_unlocked"].append(f"streak_{streak_milestone}")
                    if streak_milestone == 7:
                        user.vpn_hours_balance += REWARDS["streak_7"]
                        rewards["vpn_hours_earned"] += REWARDS["streak_7"]
                    elif streak_milestone == 30:
                        user.vpn_hours_balance += REWARDS["streak_30"]
                        rewards["vpn_hours_earned"] += REWARDS["streak_30"]
    
    user.last_activity_date = now
    
    # Проверяем довольного питомца (все статы > 80)
    if pet_state.hunger > 80 and pet_state.energy > 80 and pet_state.happiness > 80:
        # Награда за довольного питомца (раз в сутки)
        if user.last_activity_date:
            days_since = (now.date() - user.last_activity_date.date()).days
            if days_since >= 1:
                user.vpn_hours_balance += REWARDS["happy_pet_daily"]
                rewards["vpn_hours_earned"] += REWARDS["happy_pet_daily"]
    
    return rewards

@router.get("/state")
async def get_state(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepo(db)
    state = await pet_repo.get_by_user_id(user_id)
    
    if not state:
        # Create default pet state
        now = datetime.now(timezone.utc)
        state = PetState(hunger=100, energy=100, happiness=100)
        state = await pet_repo.create_for_user(user_id, state)
    
    # Apply time-based degradation
    now = datetime.now(timezone.utc)
    updated_state = apply_tick(state, now)
    
    # Save updated state
    await pet_repo.update(user_id, updated_state)
    
    return {
        "pet": {
            "hunger": updated_state.hunger,
            "energy": updated_state.energy,
            "happiness": updated_state.happiness,
            "hygiene": updated_state.hygiene,
            "health": updated_state.health,
            "discipline": updated_state.discipline,
            "is_sick": updated_state.is_sick,
            "is_sleeping": updated_state.is_sleeping,
            "light_off": updated_state.light_off,
            "needs_attention": updated_state.needs_attention,
        },
        "server_time": now.isoformat(),
        "last_activity": updated_state.last_tick_at.isoformat()
    }

@router.post("/action")
async def perform_action(
    request: ActionRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    action = request.action
    pet_repo = PetRepo(db)
    state = await pet_repo.get_by_user_id(user_id)
    
    if not state:
        now = datetime.now(timezone.utc)
        state = PetState(hunger=100, energy=100, happiness=100)
        state = await pet_repo.create_for_user(user_id, state)
    
    # Apply time-based degradation first
    now = datetime.now(timezone.utc)
    state = apply_tick(state, now)
    
    # Helper to create new state preserving all fields
    def new_state(**kwargs):
        return PetState(
            hunger=kwargs.get('hunger', state.hunger),
            energy=kwargs.get('energy', state.energy),
            happiness=kwargs.get('happiness', state.happiness),
            hygiene=kwargs.get('hygiene', state.hygiene),
            health=kwargs.get('health', state.health),
            discipline=kwargs.get('discipline', state.discipline),
            is_sick=kwargs.get('is_sick', state.is_sick),
            is_sleeping=kwargs.get('is_sleeping', state.is_sleeping),
            light_off=kwargs.get('light_off', state.light_off),
            needs_attention=kwargs.get('needs_attention', state.needs_attention),
            last_tick_at=now
        )
    
    # Apply action
    if action == "feed":
        # Если уже сыт, даём бонус к энергии
        energy_bonus = 5 if state.hunger >= 80 else 0
        state = new_state(
            hunger=clamp(state.hunger + 20),
            energy=clamp(state.energy + energy_bonus),
            happiness=clamp(state.happiness + 5),
            is_sleeping=False  # Просыпается если спал
        )
    elif action == "play":
        if state.is_sleeping:
            raise HTTPException(status_code=400, detail="Pet is sleeping! Wake it up first.")
        state = new_state(
            hunger=clamp(state.hunger - 10),
            energy=clamp(state.energy - 15),
            happiness=clamp(state.happiness + 15),
            discipline=clamp(state.discipline + 2)  # Игра немного повышает дисциплину
        )
    elif action == "sleep":
        state = new_state(
            is_sleeping=True,
            energy=clamp(state.energy + 10),  # +10 сразу при засыпании
            happiness=clamp(state.happiness + 5)
        )
    elif action == "wake":
        state = new_state(
            is_sleeping=False
        )
    elif action == "light_on":
        state = new_state(light_off=False)
    elif action == "light_off":
        state = new_state(light_off=True)
    elif action == "bath":
        # 🛁 Купание - повышает гигиену, тратит энергию
        if state.is_sleeping:
            raise HTTPException(status_code=400, detail="Pet is sleeping!")
        state = new_state(
            hygiene=clamp(state.hygiene + 40),
            energy=clamp(state.energy - 10),
            happiness=clamp(state.happiness + 10)
        )
    elif action == "heal":
        # 💊 Лечение - убирает болезнь, восстанавливает здоровье
        if not state.is_sick:
            raise HTTPException(status_code=400, detail="Pet is not sick!")
        state = new_state(
            is_sick=False,
            health=clamp(state.health + 30),
            happiness=clamp(state.happiness + 10)
        )
    elif action == "discipline":
        # 🎓 Тренировка - повышает дисциплину
        if state.is_sleeping:
            raise HTTPException(status_code=400, detail="Pet is sleeping!")
        state = new_state(
            discipline=clamp(state.discipline + 10),
            energy=clamp(state.energy - 10),
            happiness=clamp(state.happiness - 5)  # Не очень нравится
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Available: feed, play, sleep, wake, light_on, light_off, bath, heal, discipline")
    
    # Save updated state
    await pet_repo.update(user_id, state)
    
    # Обрабатываем награды
    user = await get_or_create_user(user_id, db)
    rewards = await process_action_rewards(user, action, state, db)
    await db.commit()
    
    return {
        "pet": {
            "hunger": state.hunger,
            "energy": state.energy,
            "happiness": state.happiness,
            "hygiene": state.hygiene,
            "health": state.health,
            "discipline": state.discipline,
            "is_sick": state.is_sick,
            "is_sleeping": state.is_sleeping,
            "light_off": state.light_off,
            "needs_attention": state.needs_attention,
        },
        "rewards": rewards,
        "user": {
            "level": user.level,
            "experience": user.experience,
            "streak_days": user.streak_days,
            "vpn_hours_balance": user.vpn_hours_balance
        },
        "server_time": now.isoformat()
    }

@router.post("/auth/session")
async def create_session(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    # This endpoint exists just to trigger the JWT creation flow
    # The actual JWT is returned by the dependency
    return {"message": "Session created"}


@router.post("/reset")
async def reset_pet(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Сброс питомца после смерти - весь прогресс сгорает"""
    user = await get_or_create_user(user_id, db)
    pet_repo = PetRepo(db)
    
    logger.info(f"PET DEATH RESET for user {user_id}. Level was {user.level}, XP was {user.experience}")
    
    # Сброс прогресса пользователя
    user.level = 1
    user.experience = 0
    user.streak_days = 0
    user.pet_type = None  # Требуется новый выбор питомца
    # Балансы НЕ сбрасываем (stars_balance, vpn_hours_balance)
    # Это реальные деньги
    
    # Сброс состояния питомца
    initial_state = PetState(
        hunger=100,
        energy=100,
        happiness=100,
        hygiene=100,
        health=100,
        discipline=50,
        is_sick=False,
        is_sleeping=False,
        light_off=False,
        needs_attention=False
    )
    await pet_repo.update(user_id, initial_state)
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Питомец сброшен. Выберите нового!",
        "reset_data": {
            "level": 1,
            "experience": 0,
            "streak_days": 0
        }
    }