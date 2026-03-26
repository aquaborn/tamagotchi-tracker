"""
Breeding & NFT API - скрещивание питомцев и NFT минтинг
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List
import logging

from app.deps.db import get_db
from app.deps.auth import get_current_user_id
from app.models.user import User
from app.models.pet import PetModel as Pet, PetModel
from app.services.genetics import (
    generate_genes, calculate_overall_rarity, breed_pets,
    can_breed, get_breeding_cooldown, get_stat_multiplier,
    generate_nft_metadata, get_breeding_cost,
    RARITY_MULTIPLIERS, MAX_BREEDING_COUNT
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/breeding", tags=["breeding"])


# === Pydantic Models ===
class BreedRequest(BaseModel):
    partner_pet_id: int  # Может быть < 0 для NPC


class MintNFTRequest(BaseModel):
    pet_id: int = Field(..., gt=0)


# === Helper Functions ===
async def get_user_with_pet(user_id: int, db: AsyncSession):
    """Получить пользователя и его питомца"""
    result = await db.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    result = await db.execute(select(Pet).where(Pet.user_id == user_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="У вас нет питомца")
    
    return user, pet


# === API Endpoints ===

@router.get("/status")
async def get_breeding_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Статус breeding питомца"""
    user, pet = await get_user_with_pet(user_id, db)
    
    can, reason = can_breed(
        pet.rarity or "common",
        pet.breeding_count or 0,
        pet.breeding_cooldown_until
    )
    
    return {
        "can_breed": can,
        "reason": reason if not can else None,
        "breeding_count": pet.breeding_count or 0,
        "max_breeding": MAX_BREEDING_COUNT.get(pet.rarity or "common", 5),
        "cooldown_until": pet.breeding_cooldown_until.isoformat() if pet.breeding_cooldown_until else None,
        "rarity": pet.rarity or "common",
        "genes": pet.genes or {},
        "mutations": pet.mutations or [],
        "generation": pet.generation or 0,
        "stat_multiplier": get_stat_multiplier(pet.rarity or "common", pet.mutations or [])
    }


@router.get("/partners")
async def get_available_partners(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """Получить доступных партнёров для breeding (включая NPC)"""
    user, my_pet = await get_user_with_pet(user_id, db)
    
    partners = []
    
    # === NPC ПИТОМЦЫ (всегда доступны!) ===
    npc_pets = [
        {
            "pet_id": -1,
            "owner_name": "🌳 Дикий кот",
            "pet_type": "cat",
            "rarity": "common",
            "level": 5,
            "generation": 0,
            "genes": {"color": "orange", "pattern": "stripes", "eyes": "green"},
            "breeding_cost": 50,
            "is_npc": True
        },
        {
            "pet_id": -2,
            "owner_name": "🌲 Дикий пёс",
            "pet_type": "dog",
            "rarity": "common",
            "level": 5,
            "generation": 0,
            "genes": {"color": "brown", "pattern": "solid", "eyes": "brown"},
            "breeding_cost": 50,
            "is_npc": True
        },
        {
            "pet_id": -3,
            "owner_name": "✨ Редкий лис",
            "pet_type": "fox",
            "rarity": "rare",
            "level": 10,
            "generation": 0,
            "genes": {"color": "red", "pattern": "gradient", "eyes": "amber", "trait": "cunning"},
            "breeding_cost": 150,
            "is_npc": True
        },
        {
            "pet_id": -4,
            "owner_name": "🐉 Мифический дракон",
            "pet_type": "dragon",
            "rarity": "epic",
            "level": 20,
            "generation": 0,
            "genes": {"color": "purple", "pattern": "scales", "eyes": "gold", "trait": "fire", "special": "wings"},
            "breeding_cost": 300,
            "is_npc": True
        }
    ]
    partners.extend(npc_pets)
    
    # === Игроки ===
    result = await db.execute(
        select(Pet, User)
        .join(User, Pet.user_id == User.telegram_id)
        .where(
            Pet.user_id != user_id,  # Исключаем себя
            Pet.breeding_count < max(MAX_BREEDING_COUNT.values())
        )
        .order_by(Pet.level.desc())
        .limit(limit)
    )
    
    for pet, owner in result.all():
        can, reason = can_breed(
            pet.rarity or "common",
            pet.breeding_count or 0,
            pet.breeding_cooldown_until
        )
        
        if can:
            cost = get_breeding_cost(my_pet.rarity or "common", pet.rarity or "common")
            partners.append({
                "pet_id": pet.id,
                "owner_name": owner.username or f"Player #{owner.telegram_id % 10000}",
                "pet_type": pet.pet_type or "cat",
                "rarity": pet.rarity or "common",
                "level": pet.level or 1,
                "generation": pet.generation or 0,
                "genes": pet.genes or {},
                "breeding_cost": cost,
                "is_npc": False
            })
    
    return {
        "partners": partners,
        "my_pet": {
            "rarity": my_pet.rarity or "common",
            "level": my_pet.level or 1,
            "genes": my_pet.genes or {}
        }
    }


@router.post("/breed")
async def breed_with_partner(
    request: BreedRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Скрестить питомца с партнёром (игроком или NPC)"""
    user, my_pet = await get_user_with_pet(user_id, db)
    
    # Проверяем мой питомец может breeding
    can1, reason1 = can_breed(
        my_pet.rarity or "common",
        my_pet.breeding_count or 0,
        my_pet.breeding_cooldown_until
    )
    if not can1:
        raise HTTPException(status_code=400, detail=f"Ваш питомец: {reason1}")
    
    # === NPC ПАРТНЁРЫ (id < 0) ===
    NPC_PARTNERS = {
        -1: {"rarity": "common", "genes": {"color": "orange", "pattern": "stripes", "eyes": "green"}, "cost": 50},
        -2: {"rarity": "common", "genes": {"color": "brown", "pattern": "solid", "eyes": "brown"}, "cost": 50},
        -3: {"rarity": "rare", "genes": {"color": "red", "pattern": "gradient", "eyes": "amber", "trait": "cunning"}, "cost": 150},
        -4: {"rarity": "epic", "genes": {"color": "purple", "pattern": "scales", "eyes": "gold", "trait": "fire", "special": "wings"}, "cost": 300},
    }
    
    partner_pet = None
    partner_rarity = "common"
    partner_genes = {}
    is_npc = False
    
    if request.partner_pet_id < 0:
        # NPC партнёр
        npc = NPC_PARTNERS.get(request.partner_pet_id)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC партнёр не найден")
        partner_rarity = npc["rarity"]
        partner_genes = npc["genes"]
        cost = npc["cost"]
        is_npc = True
    else:
        # Получаем партнёра-игрока
        result = await db.execute(select(Pet).where(Pet.id == request.partner_pet_id))
        partner_pet = result.scalar_one_or_none()
        if not partner_pet:
            raise HTTPException(status_code=404, detail="Партнёр не найден")
        
        # Проверяем партнёр может breeding
        can2, reason2 = can_breed(
            partner_pet.rarity or "common",
            partner_pet.breeding_count or 0,
            partner_pet.breeding_cooldown_until
        )
        if not can2:
            raise HTTPException(status_code=400, detail=f"Партнёр: {reason2}")
        
        partner_rarity = partner_pet.rarity or "common"
        partner_genes = partner_pet.genes or {}
        cost = get_breeding_cost(my_pet.rarity or "common", partner_rarity)
    
    # Проверяем стоимость
    if user.stars_balance < cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно звёзд! Нужно: {cost}, есть: {user.stars_balance}"
        )
    
    # Выполняем breeding!
    child_genes, child_rarity, mutations = breed_pets(
        my_pet.genes or {},
        partner_genes,
        my_pet.rarity or "common",
        partner_rarity
    )
    
    # Определяем поколение потомка
    partner_gen = partner_pet.generation if partner_pet else 0
    child_generation = max(my_pet.generation or 0, partner_gen or 0) + 1
    
    try:
        # Списываем звёзды
        user.stars_balance -= cost
        
        # Обновляем cooldown для моего питомца
        cooldown = get_breeding_cooldown(my_pet.rarity or "common")
        my_pet.breeding_count = (my_pet.breeding_count or 0) + 1
        my_pet.breeding_cooldown_until = datetime.now(timezone.utc) + cooldown
        
        # Обновляем партнёра (только если это игрок, не NPC)
        if partner_pet and not is_npc:
            partner_cooldown = get_breeding_cooldown(partner_rarity)
            partner_pet.breeding_count = (partner_pet.breeding_count or 0) + 1
            partner_pet.breeding_cooldown_until = datetime.now(timezone.utc) + partner_cooldown
        
        # Создаём и сохраняем нового питомца (потомок)
        child_pet = PetModel(
            user_id=my_pet.user_id,
            pet_type=child_genes.get("pet_type", my_pet.pet_type),
            genes=child_genes,
            rarity=child_rarity,
            mutations=mutations,
            generation=child_generation,
            level=1,
            experience=0,
            parent1_id=my_pet.id,
            parent2_id=partner_pet.id if partner_pet else None,
            stat_multiplier=get_stat_multiplier(child_rarity, mutations)
        )
        db.add(child_pet)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Breeding transaction failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка бридинга")
    
    logger.info(f"Breeding success: user {user_id}, rarity {child_rarity}, mutations {mutations}")
    
    return {
        "success": True,
        "child": {
            "genes": child_genes,
            "rarity": child_rarity,
            "mutations": mutations,
            "generation": child_generation,
            "stat_multiplier": get_stat_multiplier(child_rarity, mutations)
        },
        "cost_paid": cost,
        "new_balance": user.stars_balance,
        "cooldown_hours": cooldown.total_seconds() / 3600,
        "message": f"🎉 Успешное скрещивание! Редкость: {child_rarity.upper()}" + 
                   (f" + {len(mutations)} мутаций!" if mutations else "")
    }


@router.get("/nft/metadata/{pet_id}")
async def get_nft_metadata(
    pet_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Публичный endpoint для получения NFT метаданных.
    Используется маркетплейсами и кошельками.
    """
    result = await db.execute(select(Pet).where(Pet.id == pet_id))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    metadata = generate_nft_metadata(
        pet_id=pet.id,
        pet_type=pet.pet_type or "cat",
        rarity=pet.rarity or "common",
        genes=pet.genes or {},
        mutations=pet.mutations or [],
        generation=pet.generation or 0,
        level=pet.level or 1
    )
    
    return metadata


@router.post("/nft/mint")
async def mint_pet_nft(
    request: MintNFTRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Минтинг питомца как NFT.
    Требует подключённый кошелёк.
    """
    user, pet = await get_user_with_pet(user_id, db)
    
    if pet.id != request.pet_id:
        raise HTTPException(status_code=403, detail="Это не ваш питомец")
    
    if not user.wallet_address:
        raise HTTPException(status_code=400, detail="Сначала подключите TON кошелёк")
    
    if pet.nft_minted:
        return {
            "success": False,
            "message": "NFT уже сминчен",
            "nft_address": pet.nft_address
        }
    
    # Стоимость минтинга зависит от редкости
    mint_costs = {
        "common": 100,
        "uncommon": 150,
        "rare": 250,
        "epic": 400,
        "legendary": 700,
        "mythic": 1200
    }
    cost = mint_costs.get(pet.rarity or "common", 100)
    
    if user.stars_balance < cost:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно звёзд! Нужно: {cost} ⭐"
        )
    
    try:
        # Списываем звёзды
        user.stars_balance -= cost
        
        # Помечаем как сминченный (реальный минт будет через смарт-контракт)
        pet.nft_minted = True
        pet.nft_minted_at = datetime.now(timezone.utc)
        # nft_address будет установлен после реального минтинга через контракт
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"NFT mint transaction failed for user {user_id}, pet {pet.id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка минтинга NFT")
    
    metadata = generate_nft_metadata(
        pet_id=pet.id,
        pet_type=pet.pet_type or "cat",
        rarity=pet.rarity or "common",
        genes=pet.genes or {},
        mutations=pet.mutations or [],
        generation=pet.generation or 0,
        level=pet.level or 1
    )
    
    logger.info(f"NFT mint requested: pet {pet.id}, user {user_id}")
    
    return {
        "success": True,
        "message": "🎨 NFT готовится к минтингу!",
        "metadata": metadata,
        "cost_paid": cost,
        "new_balance": user.stars_balance,
        # В будущем тут будет реальная транзакция
        "pending_mint": True
    }


@router.get("/genetics/info")
async def get_genetics_info():
    """Информация о системе генетики"""
    return {
        "rarity_levels": list(RARITY_MULTIPLIERS.keys()),
        "rarity_multipliers": RARITY_MULTIPLIERS,
        "max_breeding": MAX_BREEDING_COUNT,
        "gene_types": ["color", "pattern", "eyes", "trait", "special"],
        "tips": [
            "🧬 Гены наследуются от обоих родителей",
            "✨ Мутации дают бонусные способности",
            "🎯 Редкие родители = выше шанс редкого потомка",
            "⏰ Cooldown зависит от редкости питомца",
            "🔥 Legendary мутации дают +1 к редкости"
        ]
    }
