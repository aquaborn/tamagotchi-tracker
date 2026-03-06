from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.deps.auth import get_current_user_id, require_internal_api_token
from app.deps.db import get_db
from app.models.user import User
from app.models.shop import (
    ShopItem, UserInventory, ActiveBoost, StarTransaction,
    DEFAULT_SHOP_ITEMS, MarketListing
)
from app.services.progression import EXTENDED_SHOP_ITEMS
from packages.core.core.domain.pet import PetState, clamp
from packages.core.core.repo.pet_repo import PetRepo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/shop", tags=["shop"])


# === Pydantic Models ===

class ShopItemResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price_stars: int
    effect_type: str
    effect_value: int
    effect_duration_hours: int
    emoji: str
    rarity: str
    is_available: bool
    min_level: int = 0


class PurchaseRequest(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=100)


class StarsPurchaseRequest(BaseModel):
    stars_amount: int
    purchase_type: str  # vpn, item
    item_id: Optional[int] = None


class InventoryItemResponse(BaseModel):
    id: int
    item: ShopItemResponse
    quantity: int
    is_equipped: bool


# === Helper Functions ===

async def get_or_create_user(telegram_id: int, db: AsyncSession) -> User:
    """Получает или создаёт пользователя"""
    from app.services.vpn_rewards import generate_referral_code
    
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


async def init_default_shop_items(db: AsyncSession):
    """Инициализирует магазин предметами"""
    result = await db.execute(select(ShopItem).limit(1))
    if result.scalar_one_or_none():
        return  # Магазин уже инициализирован
    
    # Используем расширенный список предметов
    all_items = EXTENDED_SHOP_ITEMS if EXTENDED_SHOP_ITEMS else DEFAULT_SHOP_ITEMS
    
    for item_data in all_items:
        item = ShopItem(**item_data)
        db.add(item)
    
    await db.commit()
    logger.info(f"Initialized {len(DEFAULT_SHOP_ITEMS)} shop items")


async def get_user_active_boosts(user_id: int, db: AsyncSession) -> dict:
    """Получает активные бусты пользователя"""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ActiveBoost)
        .where(ActiveBoost.user_id == user_id)
        .where(ActiveBoost.expires_at > now)
    )
    boosts = result.scalars().all()
    
    active = {}
    for boost in boosts:
        if boost.effect_type not in active:
            active[boost.effect_type] = boost.effect_value
        else:
            # Суммируем или берём максимум в зависимости от типа
            if boost.effect_type in ["xp_multiplier"]:
                active[boost.effect_type] = max(active[boost.effect_type], boost.effect_value)
            else:
                active[boost.effect_type] += boost.effect_value
    
    return active


async def get_equipped_bonuses(user_id: int, db: AsyncSession) -> dict:
    """Получает бонусы от экипированных предметов"""
    result = await db.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem)
        .where(UserInventory.user_id == user_id)
        .where(UserInventory.is_equipped == True)
    )
    equipped = result.all()
    
    bonuses = {}
    for inv, item in equipped:
        if item.effect_type and item.effect_value:
            if item.effect_type not in bonuses:
                bonuses[item.effect_type] = item.effect_value
            else:
                bonuses[item.effect_type] += item.effect_value
    
    return bonuses


# === Endpoints ===

@router.get("/items", response_model=List[ShopItemResponse])
async def get_shop_items(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список товаров в магазине"""
    # Инициализируем магазин если пустой
    await init_default_shop_items(db)
    
    query = select(ShopItem).where(ShopItem.is_available == True)
    if category:
        query = query.where(ShopItem.category == category)
    
    result = await db.execute(query.order_by(ShopItem.category, ShopItem.price_stars))
    items = result.scalars().all()
    
    return [
        ShopItemResponse(
            id=item.id,
            name=item.name,
            description=item.description or "",
            category=item.category,
            price_stars=item.price_stars,
            effect_type=item.effect_type or "",
            effect_value=item.effect_value or 0,
            effect_duration_hours=item.effect_duration_hours or 0,
            emoji=item.emoji or "📦",
            rarity=item.rarity or "common",
            is_available=item.is_available,
            min_level=item.min_level or 0
        )
        for item in items
    ]


@router.get("/inventory")
async def get_inventory(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить инвентарь пользователя"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem)
        .where(UserInventory.user_id == user.id)
    )
    inventory = result.all()
    
    items = []
    for inv, item in inventory:
        items.append({
            "id": inv.id,
            "item": {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "category": item.category,
                "emoji": item.emoji,
                "rarity": item.rarity,
                "effect_type": item.effect_type,
                "effect_value": item.effect_value,
                "price_stars": item.price_stars,
            },
            "quantity": inv.quantity,
            "is_equipped": inv.is_equipped
        })
    
    # Активные бусты
    boosts = await get_user_active_boosts(user.id, db)
    
    return {
        "inventory": items,
        "active_boosts": boosts,
        "equipped_count": sum(1 for i in items if i["is_equipped"])
    }


@router.post("/buy-with-balance")
async def buy_with_balance(
    request: PurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Купить предмет за внутриигровые звёзды (stars_balance)"""
    user = await get_or_create_user(user_id, db)
    
    # Получаем предмет
    result = await db.execute(
        select(ShopItem).where(ShopItem.id == request.item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not item.is_available:
        raise HTTPException(status_code=400, detail="Item unavailable")
    
    total_price = item.price_stars * request.quantity
    
    # Проверяем баланс
    if user.stars_balance < total_price:
        raise HTTPException(
            status_code=400, 
            detail=f"Not enough stars. Need {total_price}, have {user.stars_balance}"
        )
    
    # Списываем звёзды
    user.stars_balance -= total_price
    user.total_purchases += request.quantity
    
    # Barrel progress
    user.barrel_progress += request.quantity
    barrel_reward = None
    if user.barrel_progress >= 100:
        user.barrel_completions += 1
        user.barrel_progress -= 100
        user.vpn_hours_balance += 720  # 1 month VPN
        barrel_reward = "1 month VPN!"
    
    # Добавляем в инвентарь или обрабатываем эффект
    if item.category in ['clothing', 'accessory', 'food', 'toy']:
        # Проверяем есть ли уже такой предмет
        inv_result = await db.execute(
            select(UserInventory).where(
                UserInventory.user_id == user.id,
                UserInventory.item_id == item.id
            )
        )
        existing = inv_result.scalar_one_or_none()
        
        if existing:
            existing.quantity += request.quantity
        else:
            new_inv = UserInventory(
                user_id=user.id,
                item_id=item.id,
                quantity=request.quantity
            )
            db.add(new_inv)
        message = f"Added {item.name} to inventory!"
        
    elif item.category == "vpn":
        user.vpn_hours_balance += item.effect_value * request.quantity
        message = f"Got {item.effect_value * request.quantity} VPN hours!"
        
    elif item.category == "boost":
        now = datetime.now(timezone.utc)
        for _ in range(request.quantity):
            boost = ActiveBoost(
                user_id=user.id,
                item_id=item.id,
                effect_type=item.effect_type,
                effect_value=item.effect_value,
                expires_at=now + timedelta(hours=item.effect_duration_hours)
            )
            db.add(boost)
        message = f"Boost {item.name} activated!"
    else:
        message = f"Purchased {item.name}!"
    
    # Записываем транзакцию
    transaction = StarTransaction(
        user_id=user.id,
        stars_amount=total_price,
        purchase_type="item",
        purchase_item_id=item.id,
        purchase_description=f"{item.name} x{request.quantity}",
        status="completed",
        completed_at=datetime.now(timezone.utc)
    )
    db.add(transaction)
    
    await db.commit()
    
    return {
        "success": True,
        "message": message,
        "item": {
            "id": item.id,
            "name": item.name,
            "emoji": item.emoji
        },
        "new_balance": user.stars_balance,
        "barrel_progress": user.barrel_progress,
        "barrel_reward": barrel_reward
    }


@router.post("/purchase")
async def purchase_item(
    request: PurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Купить предмет за звёзды (требует предварительной оплаты через Telegram)"""
    user = await get_or_create_user(user_id, db)
    
    # Получаем предмет
    result = await db.execute(
        select(ShopItem).where(ShopItem.id == request.item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    if not item.is_available:
        raise HTTPException(status_code=400, detail="Предмет недоступен")
    
    total_price = item.price_stars * request.quantity
    
    # Здесь должна быть проверка оплаты через Telegram Stars
    # Пока просто возвращаем информацию для оплаты
    
    return {
        "item": {
            "id": item.id,
            "name": item.name,
            "price_stars": item.price_stars,
            "emoji": item.emoji
        },
        "quantity": request.quantity,
        "total_price": total_price,
        "payment_required": True,
        "message": "Для покупки отправьте звёзды через Telegram"
    }


@router.post("/confirm-purchase")
async def confirm_purchase(
    item_id: int = Query(gt=0),
    user_telegram_id: int = Query(gt=0),
    quantity: int = Query(default=1, ge=1, le=100),
    telegram_payment_id: str = Query(min_length=1, max_length=255),
    _: None = Depends(require_internal_api_token),
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить покупку после оплаты звёздами"""
    user = await get_or_create_user(user_telegram_id, db)

    existing_tx_result = await db.execute(
        select(StarTransaction).where(StarTransaction.telegram_payment_id == telegram_payment_id)
    )
    existing_tx = existing_tx_result.scalar_one_or_none()
    if existing_tx:
        return {
            "success": True,
            "already_processed": True,
            "message": "Payment already processed",
        }
    
    # Получаем предмет
    result = await db.execute(
        select(ShopItem).where(ShopItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Создаём транзакцию
    transaction = StarTransaction(
        user_id=user.id,
        telegram_payment_id=telegram_payment_id,
        stars_amount=item.price_stars * quantity,
        purchase_type="item",
        purchase_item_id=item.id,
        purchase_description=f"{item.name} x{quantity}",
        status="completed",
        completed_at=datetime.now(timezone.utc)
    )
    db.add(transaction)
    
    # Обрабатываем эффект в зависимости от категории
    if item.category == "vpn":
        # VPN часы на баланс
        user.vpn_hours_balance += item.effect_value * quantity
        message = f"Получено {item.effect_value * quantity} часов VPN!"
        
    elif item.category == "boost":
        # Активируем буст
        now = datetime.now(timezone.utc)
        for _ in range(quantity):
            boost = ActiveBoost(
                user_id=user.id,
                item_id=item.id,
                effect_type=item.effect_type,
                effect_value=item.effect_value,
                expires_at=now + timedelta(hours=item.effect_duration_hours)
            )
            db.add(boost)
        message = f"Буст '{item.name}' активирован на {item.effect_duration_hours}ч!"
        
    elif item.category in ["food"]:
        # Добавляем в инвентарь для использования
        result = await db.execute(
            select(UserInventory)
            .where(UserInventory.user_id == user.id)
            .where(UserInventory.item_id == item.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.quantity += quantity
        else:
            inv_item = UserInventory(
                user_id=user.id,
                item_id=item.id,
                quantity=quantity
            )
            db.add(inv_item)
        message = f"'{item.name}' x{quantity} добавлено в инвентарь!"
        
    elif item.category in ["clothing", "accessory"]:
        # Одежда и аксессуары - в инвентарь
        result = await db.execute(
            select(UserInventory)
            .where(UserInventory.user_id == user.id)
            .where(UserInventory.item_id == item.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.quantity += quantity
        else:
            inv_item = UserInventory(
                user_id=user.id,
                item_id=item.id,
                quantity=quantity
            )
            db.add(inv_item)
        message = f"'{item.name}' добавлено в гардероб!"
    else:
        message = f"'{item.name}' куплено!"
    
    # === БОЧКА: накопительная система ===
    barrel_reward = None
    user.total_purchases += quantity
    user.barrel_progress += quantity
    
    # Проверяем заполнение бочки (100 покупок = месяц VPN)
    if user.barrel_progress >= 100:
        user.barrel_progress -= 100  # Сбрасываем с переносом остатка
        user.barrel_completions += 1
        user.vpn_hours_balance += 720  # Месяц VPN (30 дней * 24ч)
        barrel_reward = {
            "filled": True,
            "reward": "720 часов VPN (1 месяц)",
            "completions_total": user.barrel_completions
        }
        logger.info(f"User {user_telegram_id} filled barrel #{user.barrel_completions}! +720h VPN")
    
    await db.commit()
    
    return {
        "success": True,
        "already_processed": False,
        "message": message,
        "item": item.name,
        "quantity": quantity,
        "stars_spent": item.price_stars * quantity,
        "barrel": {
            "progress": user.barrel_progress,
            "target": 100,
            "filled": barrel_reward is not None,
            "reward": barrel_reward
        }
    }


@router.post("/use-item/{inventory_id}")
async def use_item(
    inventory_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Использовать предмет из инвентаря"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem)
        .where(UserInventory.id == inventory_id)
        .where(UserInventory.user_id == user.id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Предмет не найден в инвентаре")
    
    inv, item = row
    
    if inv.quantity <= 0:
        raise HTTPException(status_code=400, detail="Предмет закончился")
    
    pet_repo = PetRepo(db)
    pet_state = await pet_repo.get_by_user_id(user_id)
    
    if not pet_state:
        raise HTTPException(status_code=404, detail="Питомец не найден")
    
    # Применяем эффект
    message = ""
    def with_updates(**kwargs) -> PetState:
        return PetState(
            hunger=kwargs.get("hunger", pet_state.hunger),
            energy=kwargs.get("energy", pet_state.energy),
            happiness=kwargs.get("happiness", pet_state.happiness),
            hygiene=kwargs.get("hygiene", pet_state.hygiene),
            health=kwargs.get("health", pet_state.health),
            discipline=kwargs.get("discipline", pet_state.discipline),
            is_sick=kwargs.get("is_sick", pet_state.is_sick),
            is_sleeping=kwargs.get("is_sleeping", pet_state.is_sleeping),
            light_off=kwargs.get("light_off", pet_state.light_off),
            needs_attention=kwargs.get("needs_attention", pet_state.needs_attention),
            last_tick_at=pet_state.last_tick_at
        )
    
    if item.effect_type == "hunger_restore":
        new_hunger = clamp(pet_state.hunger + item.effect_value)
        pet_state = with_updates(hunger=new_hunger)
        message = f"Сытость восстановлена до {new_hunger}!"
        
    elif item.effect_type == "energy_restore":
        new_energy = clamp(pet_state.energy + item.effect_value)
        pet_state = with_updates(energy=new_energy)
        message = f"Энергия восстановлена до {new_energy}!"
        
    elif item.effect_type == "hunger_happiness_restore":
        new_hunger = clamp(pet_state.hunger + item.effect_value)
        new_happiness = clamp(pet_state.happiness + 10)
        pet_state = with_updates(hunger=new_hunger, happiness=new_happiness)
        message = f"Сытость: {new_hunger}, Счастье: {new_happiness}!"
        
    elif item.effect_type == "full_restore":
        pet_state = with_updates(hunger=100, energy=100, happiness=100, hygiene=100, health=100)
        message = "Все статы восстановлены до 100!"
    else:
        raise HTTPException(status_code=400, detail="Этот предмет нельзя использовать")
    
    # Сохраняем состояние питомца
    await pet_repo.update(user_id, pet_state)
    
    # Уменьшаем количество
    inv.quantity -= 1
    if inv.quantity <= 0:
        await db.delete(inv)
    
    await db.commit()
    
    return {
        "success": True,
        "message": message,
        "pet": {
            "hunger": pet_state.hunger,
            "energy": pet_state.energy,
            "happiness": pet_state.happiness
        },
        "item_remaining": max(0, inv.quantity)
    }


@router.post("/equip/{inventory_id}")
async def equip_item(
    inventory_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Экипировать предмет (одежда/аксессуары)"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem)
        .where(UserInventory.id == inventory_id)
        .where(UserInventory.user_id == user.id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    inv, item = row
    
    if item.category not in ["clothing", "accessory"]:
        raise HTTPException(status_code=400, detail="Этот предмет нельзя экипировать")
    
    # Снимаем текущий предмет той же категории
    result = await db.execute(
        select(UserInventory)
        .join(ShopItem)
        .where(UserInventory.user_id == user.id)
        .where(UserInventory.is_equipped == True)
        .where(ShopItem.category == item.category)
    )
    currently_equipped = result.scalars().all()
    
    for eq in currently_equipped:
        eq.is_equipped = False
    
    # Экипируем новый
    inv.is_equipped = True
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"'{item.name}' экипирован!",
        "effect": {
            "type": item.effect_type,
            "value": item.effect_value
        }
    }


@router.post("/unequip/{inventory_id}")
async def unequip_item(
    inventory_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Снять предмет"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(UserInventory)
        .where(UserInventory.id == inventory_id)
        .where(UserInventory.user_id == user.id)
    )
    inv = result.scalar_one_or_none()
    
    if not inv:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    inv.is_equipped = False
    await db.commit()
    
    return {"success": True, "message": "Предмет снят"}


async def get_active_boosts_list(user_id: int, db: AsyncSession) -> list:
    """Internal function to get active boosts as list"""
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return []
    
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ActiveBoost, ShopItem)
        .join(ShopItem)
        .where(ActiveBoost.user_id == user.id)
        .where(ActiveBoost.expires_at > now)
    )
    boosts = result.all()
    
    return [
        {
            "id": boost.id,
            "effect_type": boost.effect_type,
            "effect_value": boost.effect_value,
        }
        for boost, item in boosts
    ]


@router.get("/active-boosts")
async def get_active_boosts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить активные бусты"""
    user = await get_or_create_user(user_id, db)
    
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ActiveBoost, ShopItem)
        .join(ShopItem)
        .where(ActiveBoost.user_id == user.id)
        .where(ActiveBoost.expires_at > now)
    )
    boosts = result.all()
    
    return {
        "active_boosts": [
            {
                "id": boost.id,
                "name": item.name,
                "emoji": item.emoji,
                "effect_type": boost.effect_type,
                "effect_value": boost.effect_value,
                "expires_at": boost.expires_at.isoformat(),
                "hours_remaining": int((boost.expires_at - now).total_seconds() / 3600)
            }
            for boost, item in boosts
        ]
    }


@router.get("/prices")
async def get_star_prices():
    """Получить цены в звёздах"""
    return {
        "vpn_packages": [
            {"name": "3 дня", "stars": 30, "hours": 72},
            {"name": "1 неделя", "stars": 60, "hours": 168},
            {"name": "2 недели", "stars": 100, "hours": 336},
            {"name": "1 месяц", "stars": 180, "hours": 720},
        ],
        "categories": [
            {"id": "food", "name": "Еда", "emoji": "🍖"},
            {"id": "boost", "name": "Бусты", "emoji": "⚡"},
            {"id": "clothing", "name": "Одежда", "emoji": "👕"},
            {"id": "accessory", "name": "Аксессуары", "emoji": "💎"},
            {"id": "vpn", "name": "VPN", "emoji": "🛡️"},
        ]
    }


@router.get("/barrel")
async def get_barrel_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить статус бочки"""
    user = await get_or_create_user(user_id, db)
    
    progress_percent = (user.barrel_progress / 100) * 100
    purchases_left = 100 - user.barrel_progress
    
    return {
        "barrel": {
            "progress": user.barrel_progress,
            "target": 100,
            "progress_percent": round(progress_percent, 1),
            "purchases_left": purchases_left,
            "completions": user.barrel_completions,
            "total_purchases": user.total_purchases,
            "reward": "720 часов VPN (1 месяц)",
            "emoji": "🛢️"
        },
        "message": f"До награды: {purchases_left} покупок" if purchases_left > 0 else "Бочка заполнена!"
    }


# === P2P MARKETPLACE ===

MARKET_COMMISSION = 0.03  # 3% комиссия


class CreateListingRequest(BaseModel):
    inventory_id: int = Field(gt=0)
    price: int = Field(ge=1)
    quantity: int = Field(default=1, ge=1, le=100)


class BuyListingRequest(BaseModel):
    listing_id: int


@router.get("/market")
async def get_market_listings(
    category: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Получить активные листинги маркетплейса"""
    query = select(MarketListing, ShopItem, User).join(
        ShopItem, MarketListing.item_id == ShopItem.id
    ).join(
        User, MarketListing.seller_id == User.id
    ).where(MarketListing.status == "active")
    
    if category:
        query = query.where(ShopItem.category == category)
    
    result = await db.execute(query.order_by(MarketListing.listed_at.desc()).limit(50))
    listings = result.all()
    
    items = []
    for listing, item, seller in listings:
        items.append({
            "id": listing.id,
            "item": {
                "id": item.id,
                "name": item.name,
                "emoji": item.emoji,
                "category": item.category,
                "rarity": item.rarity,
                "original_price": item.price_stars,
            },
            "price": listing.price,
            "quantity": listing.quantity,
            "seller": {
                "id": seller.telegram_id,
                "name": seller.first_name or seller.username or f"User#{seller.id}",
            },
            "is_own": seller.telegram_id == user_id,
            "listed_at": listing.listed_at.isoformat() if listing.listed_at else None,
        })
    
    return {
        "listings": items,
        "commission": f"{int(MARKET_COMMISSION * 100)}%",
        "total": len(items)
    }


@router.post("/market/list")
async def create_listing(
    request: CreateListingRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Выставить предмет на продажу"""
    user = await get_or_create_user(user_id, db)
    
    # Проверяем что предмет есть в инвентаре
    result = await db.execute(
        select(UserInventory).where(
            UserInventory.id == request.inventory_id,
            UserInventory.user_id == user.id
        )
    )
    inventory_item = result.scalar_one_or_none()
    
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Item not found in inventory")
    
    if inventory_item.quantity < request.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity")
    
    if inventory_item.is_equipped:
        raise HTTPException(status_code=400, detail="Unequip item first")
    
    # Проверяем цену (минимум 1 звезда)
    if request.price < 1:
        raise HTTPException(status_code=400, detail="Price must be at least 1")
    
    # Проверяем что нет активного листинга
    existing = await db.execute(
        select(MarketListing).where(
            MarketListing.inventory_id == request.inventory_id,
            MarketListing.status == "active"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Item already listed")
    
    # Создаём листинг
    listing = MarketListing(
        seller_id=user.id,
        inventory_id=inventory_item.id,
        item_id=inventory_item.item_id,
        price=request.price,
        quantity=request.quantity,
        status="active"
    )
    db.add(listing)
    await db.commit()
    
    return {
        "success": True,
        "listing_id": listing.id,
        "message": f"Item listed for {request.price} ⭐"
    }


@router.post("/market/buy")
async def buy_from_market(
    request: BuyListingRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Купить предмет с маркетплейса"""
    buyer = await get_or_create_user(user_id, db)
    
    # Получаем листинг
    result = await db.execute(
        select(MarketListing).where(
            MarketListing.id == request.listing_id,
            MarketListing.status == "active"
        )
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or sold")
    
    # Нельзя купить свой товар
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot buy your own item")
    
    # Проверяем баланс
    if buyer.stars_balance < listing.price:
        raise HTTPException(status_code=400, detail="Not enough stars")
    
    # Получаем продавца
    seller_result = await db.execute(select(User).where(User.id == listing.seller_id))
    seller = seller_result.scalar_one()
    
    # Рассчитываем комиссию
    commission = int(listing.price * MARKET_COMMISSION)
    seller_receives = listing.price - commission
    
    # Списываем у покупателя
    buyer.stars_balance -= listing.price
    
    # Начисляем продавцу (минус комиссия)
    seller.stars_balance += seller_receives
    
    # Получаем inventory продавца
    seller_inv_result = await db.execute(
        select(UserInventory).where(UserInventory.id == listing.inventory_id)
    )
    seller_inventory = seller_inv_result.scalar_one()
    
    # Уменьшаем количество у продавца
    seller_inventory.quantity -= listing.quantity
    if seller_inventory.quantity <= 0:
        await db.delete(seller_inventory)
    
    # Добавляем покупателю
    buyer_inv_result = await db.execute(
        select(UserInventory).where(
            UserInventory.user_id == buyer.id,
            UserInventory.item_id == listing.item_id
        )
    )
    buyer_inventory = buyer_inv_result.scalar_one_or_none()
    
    if buyer_inventory:
        buyer_inventory.quantity += listing.quantity
    else:
        buyer_inventory = UserInventory(
            user_id=buyer.id,
            item_id=listing.item_id,
            quantity=listing.quantity
        )
        db.add(buyer_inventory)
    
    # Обновляем листинг
    listing.status = "sold"
    listing.buyer_id = buyer.id
    listing.sold_at = datetime.now(timezone.utc)
    
    # Записываем транзакцию
    tx = StarTransaction(
        user_id=buyer.id,
        stars_amount=listing.price,
        purchase_type="market_purchase",
        purchase_description=f"Bought from market (listing #{listing.id})",
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(tx)
    
    tx_seller = StarTransaction(
        user_id=seller.id,
        stars_amount=seller_receives,
        purchase_type="market_sale",
        purchase_description=f"Market sale (commission: {commission} ⭐)",
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(tx_seller)
    
    await db.commit()
    
    return {
        "success": True,
        "price_paid": listing.price,
        "seller_received": seller_receives,
        "commission": commission,
        "new_balance": buyer.stars_balance,
        "message": f"Purchased for {listing.price} ⭐ (commission: {commission} ⭐)"
    }


@router.post("/market/cancel/{listing_id}")
async def cancel_listing(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Отменить листинг"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(MarketListing).where(
            MarketListing.id == listing_id,
            MarketListing.seller_id == user.id,
            MarketListing.status == "active"
        )
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing.status = "cancelled"
    await db.commit()
    
    return {"success": True, "message": "Listing cancelled"}


@router.get("/market/my")
async def get_my_listings(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Мои активные листинги"""
    user = await get_or_create_user(user_id, db)
    
    result = await db.execute(
        select(MarketListing, ShopItem).join(
            ShopItem, MarketListing.item_id == ShopItem.id
        ).where(
            MarketListing.seller_id == user.id,
            MarketListing.status == "active"
        )
    )
    listings = result.all()
    
    items = []
    for listing, item in listings:
        items.append({
            "id": listing.id,
            "item": {
                "name": item.name,
                "emoji": item.emoji,
            },
            "price": listing.price,
            "quantity": listing.quantity,
            "listed_at": listing.listed_at.isoformat() if listing.listed_at else None,
        })
    
    return {"listings": items, "total": len(items)}
