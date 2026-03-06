from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.pet import Base


class ShopItem(Base):
    """Предметы в магазине"""
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # food, clothing, accessory, boost
    
    # Цена в звёздах
    price_stars = Column(Integer, nullable=False)
    
    # Эффекты
    effect_type = Column(String(50))  # hunger_boost, energy_boost, xp_multiplier, vpn_hours
    effect_value = Column(Integer, default=0)  # Значение эффекта
    effect_duration_hours = Column(Integer, default=0)  # Длительность (0 = постоянный)
    
    # Визуал
    emoji = Column(String(10))
    image_url = Column(String(255))
    
    # Редкость
    rarity = Column(String(20), default="common")  # common, rare, epic, legendary
    
    # Доступность
    is_available = Column(Boolean, default=True)
    limited_quantity = Column(Integer, nullable=True)  # None = безлимит
    min_level = Column(Integer, default=0)  # Минимальный уровень для покупки
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserInventory(Base):
    """Инвентарь пользователя"""
    __tablename__ = "user_inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    
    quantity = Column(Integer, default=1)
    is_equipped = Column(Boolean, default=False)  # Для одежды/аксессуаров
    
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    item = relationship("ShopItem")


class ActiveBoost(Base):
    """Активные бусты пользователя"""
    __tablename__ = "active_boosts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    
    effect_type = Column(String(50), nullable=False)
    effect_value = Column(Integer, nullable=False)
    
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    item = relationship("ShopItem")


class MarketListing(Base):
    """P2P Marketplace - листинги игроков"""
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("user_inventory.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    
    # Цена продажи (устанавливает продавец)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    
    # Статус
    status = Column(String(20), default="active")  # active, sold, cancelled
    
    # Timestamps
    listed_at = Column(DateTime(timezone=True), server_default=func.now())
    sold_at = Column(DateTime(timezone=True), nullable=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    seller = relationship("User", foreign_keys=[seller_id])
    buyer = relationship("User", foreign_keys=[buyer_id])
    item = relationship("ShopItem")
    inventory = relationship("UserInventory")


class StarTransaction(Base):
    """История транзакций звёзд"""
    __tablename__ = "star_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Telegram payment
    telegram_payment_id = Column(String(255), unique=True)
    
    # Сумма
    stars_amount = Column(Integer, nullable=False)
    
    # Что купили
    purchase_type = Column(String(50), nullable=False)  # vpn, item, stars_pack
    purchase_item_id = Column(Integer, nullable=True)
    purchase_description = Column(String(255))
    
    # Статус
    status = Column(String(20), default="pending")  # pending, completed, refunded
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


# Конфигурация магазина - предметы по умолчанию
DEFAULT_SHOP_ITEMS = [
    # === КОРМ (food) ===
    {
        "name": "Обычный корм",
        "description": "Восстанавливает 20 сытости",
        "category": "food",
        "price_stars": 5,
        "effect_type": "hunger_restore",
        "effect_value": 20,
        "emoji": "🍖",
        "rarity": "common"
    },
    {
        "name": "Премиум корм",
        "description": "Восстанавливает 50 сытости и +10 счастья",
        "category": "food",
        "price_stars": 15,
        "effect_type": "hunger_happiness_restore",
        "effect_value": 50,
        "emoji": "🥩",
        "rarity": "rare"
    },
    {
        "name": "Супер-еда",
        "description": "Полностью восстанавливает все статы",
        "category": "food",
        "price_stars": 30,
        "effect_type": "full_restore",
        "effect_value": 100,
        "emoji": "🍱",
        "rarity": "epic"
    },
    {
        "name": "Энергетик",
        "description": "Восстанавливает 30 энергии",
        "category": "food",
        "price_stars": 10,
        "effect_type": "energy_restore",
        "effect_value": 30,
        "emoji": "⚡",
        "rarity": "common"
    },
    
    # === БУСТЫ (boost) ===
    {
        "name": "XP Буст x2",
        "description": "Двойной опыт на 24 часа",
        "category": "boost",
        "price_stars": 50,
        "effect_type": "xp_multiplier",
        "effect_value": 2,
        "effect_duration_hours": 24,
        "emoji": "⭐",
        "rarity": "rare"
    },
    {
        "name": "XP Буст x3",
        "description": "Тройной опыт на 12 часов",
        "category": "boost",
        "price_stars": 75,
        "effect_type": "xp_multiplier",
        "effect_value": 3,
        "effect_duration_hours": 12,
        "emoji": "🌟",
        "rarity": "epic"
    },
    {
        "name": "Замедление голода",
        "description": "Питомец голодает в 2 раза медленнее (48ч)",
        "category": "boost",
        "price_stars": 40,
        "effect_type": "hunger_slow",
        "effect_value": 2,
        "effect_duration_hours": 48,
        "emoji": "🐢",
        "rarity": "rare"
    },
    {
        "name": "Автокормушка",
        "description": "Автоматически кормит питомца 7 дней",
        "category": "boost",
        "price_stars": 100,
        "effect_type": "auto_feed",
        "effect_value": 1,
        "effect_duration_hours": 168,
        "emoji": "🤖",
        "rarity": "legendary"
    },
    
    # === ОДЕЖДА (clothing) ===
    {
        "name": "Красный шарфик",
        "description": "+5% к получаемому опыту",
        "category": "clothing",
        "price_stars": 25,
        "effect_type": "xp_bonus_percent",
        "effect_value": 5,
        "emoji": "🧣",
        "rarity": "common"
    },
    {
        "name": "Модная шляпа",
        "description": "+10% к получаемому опыту",
        "category": "clothing",
        "price_stars": 50,
        "effect_type": "xp_bonus_percent",
        "effect_value": 10,
        "emoji": "🎩",
        "rarity": "rare"
    },
    {
        "name": "Королевская корона",
        "description": "+25% к получаемому опыту",
        "category": "clothing",
        "price_stars": 150,
        "effect_type": "xp_bonus_percent",
        "effect_value": 25,
        "emoji": "👑",
        "rarity": "legendary"
    },
    {
        "name": "Свитер",
        "description": "Энергия тратится на 10% медленнее",
        "category": "clothing",
        "price_stars": 35,
        "effect_type": "energy_save_percent",
        "effect_value": 10,
        "emoji": "🧥",
        "rarity": "rare"
    },
    
    # === АКСЕССУАРЫ (accessory) ===
    {
        "name": "Простой ошейник",
        "description": "Базовый ошейник для питомца",
        "category": "accessory",
        "price_stars": 10,
        "effect_type": "cosmetic",
        "effect_value": 0,
        "emoji": "📿",
        "rarity": "common"
    },
    {
        "name": "Золотой ошейник",
        "description": "+5% к VPN наградам",
        "category": "accessory",
        "price_stars": 80,
        "effect_type": "vpn_bonus_percent",
        "effect_value": 5,
        "emoji": "💎",
        "rarity": "epic"
    },
    {
        "name": "Счастливый талисман",
        "description": "+15% к счастью от всех действий",
        "category": "accessory",
        "price_stars": 60,
        "effect_type": "happiness_bonus_percent",
        "effect_value": 15,
        "emoji": "🍀",
        "rarity": "rare"
    },
    {
        "name": "Магический амулет",
        "description": "Шанс x2 награды за действие (10%)",
        "category": "accessory",
        "price_stars": 200,
        "effect_type": "double_reward_chance",
        "effect_value": 10,
        "emoji": "🔮",
        "rarity": "legendary"
    },
    
    # === VPN ПАКЕТЫ (vpn) ===
    {
        "name": "VPN 3 дня",
        "description": "72 часа VPN доступа",
        "category": "vpn",
        "price_stars": 30,
        "effect_type": "vpn_hours",
        "effect_value": 72,
        "emoji": "🛡️",
        "rarity": "common"
    },
    {
        "name": "VPN 1 неделя",
        "description": "168 часов VPN доступа",
        "category": "vpn",
        "price_stars": 60,
        "effect_type": "vpn_hours",
        "effect_value": 168,
        "emoji": "🔐",
        "rarity": "rare"
    },
    {
        "name": "VPN 2 недели",
        "description": "336 часов VPN доступа",
        "category": "vpn",
        "price_stars": 100,
        "effect_type": "vpn_hours",
        "effect_value": 336,
        "emoji": "🏰",
        "rarity": "epic"
    },
    {
        "name": "VPN 1 месяц",
        "description": "720 часов VPN доступа",
        "category": "vpn",
        "price_stars": 180,
        "effect_type": "vpn_hours",
        "effect_value": 720,
        "emoji": "🚀",
        "rarity": "legendary"
    },
]
