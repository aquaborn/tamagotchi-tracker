"""
Система прогрессии питомца - эволюция, уровни, бонусы
"""

# === ЭВОЛЮЦИЯ ПИТОМЦА ===
# Питомец меняет внешний вид и получает бонусы при достижении уровней

PET_EVOLUTIONS = {
    1: {
        "name": "Малыш",
        "emoji": "🐣",
        "description": "Маленький и милый питомец",
        "color": "#FFB347",  # Оранжевый
        "size": 1.0,
        "unlocks": ["Базовые действия: кормить, играть, спать"]
    },
    5: {
        "name": "Котёнок",
        "emoji": "🐱",
        "description": "Подросший игривый котёнок",
        "color": "#FFB347",
        "size": 1.1,
        "unlocks": ["Новые эмоции", "Ошейники в магазине"],
        "bonus": {"xp_multiplier": 1.05}  # +5% XP
    },
    10: {
        "name": "Кот",
        "emoji": "😺",
        "description": "Взрослый умный кот",
        "color": "#FFA500",
        "size": 1.2,
        "unlocks": ["Шляпы и одежда", "Редкие предметы"],
        "bonus": {"xp_multiplier": 1.1, "hunger_slow": 0.95}  # +10% XP, -5% голод
    },
    20: {
        "name": "Мудрый кот",
        "emoji": "😸",
        "description": "Опытный и мудрый питомец",
        "color": "#FF8C00",
        "size": 1.3,
        "unlocks": ["Эпические предметы", "Специальные бусты"],
        "bonus": {"xp_multiplier": 1.15, "hunger_slow": 0.9, "vpn_bonus": 1.1}
    },
    35: {
        "name": "Мастер",
        "emoji": "😻",
        "description": "Мастер своего дела",
        "color": "#FF6347",
        "size": 1.4,
        "unlocks": ["Легендарные предметы", "Уникальные скины"],
        "bonus": {"xp_multiplier": 1.2, "hunger_slow": 0.85, "vpn_bonus": 1.2}
    },
    50: {
        "name": "Легенда",
        "emoji": "🦁",
        "description": "Легендарный питомец!",
        "color": "#FFD700",  # Золотой
        "size": 1.5,
        "unlocks": ["Золотой скин", "VIP статус", "Эксклюзивные награды"],
        "bonus": {"xp_multiplier": 1.3, "hunger_slow": 0.8, "vpn_bonus": 1.5}
    },
    75: {
        "name": "Мифический",
        "emoji": "🐉",
        "description": "Мифическое существо невероятной силы",
        "color": "#9400D3",  # Фиолетовый
        "size": 1.6,
        "unlocks": ["Мифический скин", "Аура"],
        "bonus": {"xp_multiplier": 1.5, "hunger_slow": 0.7, "vpn_bonus": 2.0}
    },
    100: {
        "name": "Божественный",
        "emoji": "✨",
        "description": "Достиг божественного уровня!",
        "color": "#FFFFFF",  # Белый с сиянием
        "size": 1.7,
        "unlocks": ["Божественный скин", "Бессмертие (не умирает от голода)", "Максимальные бонусы"],
        "bonus": {"xp_multiplier": 2.0, "hunger_slow": 0.5, "vpn_bonus": 3.0, "immortal": True}
    }
}

# === НАГРАДЫ ЗА УРОВНИ ===
LEVEL_REWARDS = {
    5: {"vpn_hours": 24, "title": "Первые шаги"},
    10: {"vpn_hours": 48, "title": "Растущий"},
    15: {"vpn_hours": 48, "title": "Подросток"},
    20: {"vpn_hours": 72, "title": "Взрослый"},
    25: {"vpn_hours": 72, "title": "Опытный"},
    30: {"vpn_hours": 96, "title": "Ветеран"},
    35: {"vpn_hours": 120, "title": "Мастер"},
    40: {"vpn_hours": 120, "title": "Эксперт"},
    45: {"vpn_hours": 168, "title": "Гуру"},
    50: {"vpn_hours": 240, "title": "Легенда"},  # 10 дней!
    60: {"vpn_hours": 336, "title": "Эпический"},  # 2 недели
    75: {"vpn_hours": 504, "title": "Мифический"},  # 3 недели
    100: {"vpn_hours": 720, "title": "Божественный"},  # Месяц!
}

# === РАСШИРЕННЫЙ МАГАЗИН ===
# FOOD: One-time use items that restore pet stats. Use from inventory.
# BOOST: Temporary effects that last for specified hours. Auto-activates on purchase.
# CLOTHING: Permanent bonuses while equipped. Only 1 can be worn at a time.
# ACCESSORY: Special effects while equipped. Only 1 can be worn at a time.
# VPN: Direct VPN hours added to your balance.

EXTENDED_SHOP_ITEMS = [
    # ==========================================
    # КОРМ (food) - восстанавливает статы при использовании
    # ==========================================
    
    # Базовый корм
    {"name": "Сухарик", "description": "🍖+10 hunger. Use from inventory to feed pet.", "category": "food", "price_stars": 2,
     "effect_type": "hunger_restore", "effect_value": 10, "emoji": "🍪", "rarity": "common"},
    
    {"name": "Молоко", "description": "🍖+15 hunger, 😊+5 happy. Tasty milk!", "category": "food", "price_stars": 5,
     "effect_type": "hunger_happiness", "effect_value": 15, "emoji": "🥛", "rarity": "common"},
    
    {"name": "Рыбка", "description": "🍖+25 hunger. Fish is pet's favorite!", "category": "food", "price_stars": 8,
     "effect_type": "hunger_restore", "effect_value": 25, "emoji": "🐟", "rarity": "common"},
    
    {"name": "Мясо", "description": "🍖+35 hunger. Premium meat for hungry pet.", "category": "food", "price_stars": 12,
     "effect_type": "hunger_restore", "effect_value": 35, "emoji": "🍖", "rarity": "common"},
    
    {"name": "Стейк", "description": "🍖+50 hunger, 😊+10 happy. Juicy steak!", "category": "food", "price_stars": 20,
     "effect_type": "hunger_happiness", "effect_value": 50, "emoji": "🥩", "rarity": "rare"},
    
    {"name": "Суши сет", "description": "🍖+60 hunger, 😊+15 happy, ⚡+10 energy", "category": "food", "price_stars": 35,
     "effect_type": "multi_restore", "effect_value": 60, "emoji": "🍣", "rarity": "rare"},
    
    {"name": "Королевский пир", "description": "🔥FULL RESTORE all stats to 100%!", "category": "food", "price_stars": 50,
     "effect_type": "full_restore", "effect_value": 100, "emoji": "👑🍽️", "rarity": "epic"},
    
    {"name": "Божественный нектар", "description": "✨MAX stats + 1h all boosts! LVL50+", "category": "food", "price_stars": 100,
     "effect_type": "divine_restore", "effect_value": 100, "emoji": "✨🍷", "rarity": "legendary",
     "min_level": 50},
    
    # ==========================================
    # ЭНЕРГЕТИКИ (energy) - энергия и бодрость
    # ==========================================
    
    {"name": "Кофе", "description": "⚡+20 energy. Wake up your pet!", "category": "food", "price_stars": 5,
     "effect_type": "energy_restore", "effect_value": 20, "emoji": "☕", "rarity": "common"},
    
    {"name": "Энергетик", "description": "⚡+35 energy. Power drink!", "category": "food", "price_stars": 10,
     "effect_type": "energy_restore", "effect_value": 35, "emoji": "🥤", "rarity": "common"},
    
    {"name": "Двойной эспрессо", "description": "⚡+50 energy. Double shot!", "category": "food", "price_stars": 18,
     "effect_type": "energy_restore", "effect_value": 50, "emoji": "☕☕", "rarity": "rare"},
    
    {"name": "Энерго-бомба", "description": "⚡+80 energy, 😊+20 happy. BOOM!", "category": "food", "price_stars": 30,
     "effect_type": "energy_happiness", "effect_value": 80, "emoji": "💥⚡", "rarity": "epic"},
    
    {"name": "Молния Зевса", "description": "⚡MAX energy + x2 action speed 1h! LVL35+", "category": "food", "price_stars": 60,
     "effect_type": "zeus_bolt", "effect_value": 100, "emoji": "⚡🔱", "rarity": "legendary",
     "min_level": 35},
    
    # ==========================================
    # ЛАКОМСТВА (treats) - счастье
    # ==========================================
    
    {"name": "Печенька", "description": "😊+15 happiness. Sweet treat!", "category": "food", "price_stars": 5,
     "effect_type": "happiness_restore", "effect_value": 15, "emoji": "🍪", "rarity": "common"},
    
    {"name": "Мороженое", "description": "😊+25 happiness. Cold and yummy!", "category": "food", "price_stars": 10,
     "effect_type": "happiness_restore", "effect_value": 25, "emoji": "🍦", "rarity": "common"},
    
    {"name": "Торт", "description": "😊+40 happy, 🍖+10 hunger. Party cake!", "category": "food", "price_stars": 20,
     "effect_type": "happiness_hunger", "effect_value": 40, "emoji": "🎂", "rarity": "rare"},
    
    {"name": "Радужный кекс", "description": "😊+60 happy + rainbow visual effect!", "category": "food", "price_stars": 35,
     "effect_type": "rainbow_happiness", "effect_value": 60, "emoji": "🧁🌈", "rarity": "epic"},
    
    {"name": "Эликсир счастья", "description": "😊Happiness locked at MAX for 24h! LVL20+", "category": "food", "price_stars": 80,
     "effect_type": "happiness_lock", "effect_value": 100, "emoji": "🧪💖", "rarity": "legendary",
     "effect_duration_hours": 24, "min_level": 20},
    
    # ==========================================
    # БУСТЫ (boost) - временные усиления (auto-activate on purchase)
    # ==========================================
    
    # XP бусты
    {"name": "XP Boost x1.5", "description": "📈+50% XP for 6h. Level up faster!", "category": "boost", "price_stars": 25,
     "effect_type": "xp_multiplier", "effect_value": 1.5, "effect_duration_hours": 6,
     "emoji": "📈", "rarity": "common"},
    
    {"name": "XP Boost x2", "description": "⭐DOUBLE XP for 12h! Best value.", "category": "boost", "price_stars": 50,
     "effect_type": "xp_multiplier", "effect_value": 2, "effect_duration_hours": 12,
     "emoji": "⭐", "rarity": "rare"},
    
    {"name": "XP Boost x3", "description": "🌟TRIPLE XP for 6h! Super fast!", "category": "boost", "price_stars": 75,
     "effect_type": "xp_multiplier", "effect_value": 3, "effect_duration_hours": 6,
     "emoji": "🌟", "rarity": "epic"},
    
    {"name": "XP Boost x5", "description": "💫x5 XP for 3h! Max speed! LVL25+", "category": "boost", "price_stars": 120,
     "effect_type": "xp_multiplier", "effect_value": 5, "effect_duration_hours": 3,
     "emoji": "💫", "rarity": "legendary", "min_level": 25},
    
    # Замедление статов
    {"name": "Сытый желудок", "description": "🐢Hunger drops 30% slower for 24h", "category": "boost", "price_stars": 30,
     "effect_type": "hunger_slow", "effect_value": 0.7, "effect_duration_hours": 24,
     "emoji": "🐢", "rarity": "rare"},
    
    {"name": "Вечная энергия", "description": "🔋Energy drops 30% slower for 24h", "category": "boost", "price_stars": 30,
     "effect_type": "energy_slow", "effect_value": 0.7, "effect_duration_hours": 24,
     "emoji": "🔋", "rarity": "rare"},
    
    {"name": "Счастливчик", "description": "🍀Happiness stays at 100% for 24h!", "category": "boost", "price_stars": 40,
     "effect_type": "happiness_lock", "effect_value": 1, "effect_duration_hours": 24,
     "emoji": "🍀", "rarity": "epic"},
    
    # Автоматизация
    {"name": "Автокормушка", "description": "🤖Auto-feeds pet for 3 days. AFK mode!", "category": "boost", "price_stars": 60,
     "effect_type": "auto_feed", "effect_value": 1, "effect_duration_hours": 72,
     "emoji": "🤖🍖", "rarity": "rare"},
    
    {"name": "Автокормушка PRO", "description": "🤖Auto-feeds pet for 7 days. Vacation mode!", "category": "boost", "price_stars": 120,
     "effect_type": "auto_feed", "effect_value": 1, "effect_duration_hours": 168,
     "emoji": "🤖⭐", "rarity": "epic"},
    
    {"name": "Полная автоматика", "description": "👑ALL stats auto-maintained 7 days! LVL30+", "category": "boost", "price_stars": 200,
     "effect_type": "auto_all", "effect_value": 1, "effect_duration_hours": 168,
     "emoji": "🤖👑", "rarity": "legendary", "min_level": 30},
    
    # VPN бонусы
    {"name": "VPN Boost", "description": "🛡️+20% VPN rewards for 24h", "category": "boost", "price_stars": 40,
     "effect_type": "vpn_bonus", "effect_value": 1.2, "effect_duration_hours": 24,
     "emoji": "🛡️📈", "rarity": "rare"},
    
    {"name": "VPN Boost PRO", "description": "🛡️+50% VPN rewards for 24h! LVL15+", "category": "boost", "price_stars": 80,
     "effect_type": "vpn_bonus", "effect_value": 1.5, "effect_duration_hours": 24,
     "emoji": "🛡️⭐", "rarity": "epic", "min_level": 15},
    
    # ==========================================
    # ОДЕЖДА (clothing) - PERMANENT bonuses while equipped
    # ==========================================
    
    # Шапки
    {"name": "Бантик", "description": "🎀+3% XP always! Equip in wardrobe.", "category": "clothing", "price_stars": 15,
     "effect_type": "xp_bonus_percent", "effect_value": 3, "emoji": "🎀", "rarity": "common"},
    
    {"name": "Бейсболка", "description": "🧢+5% XP always! Casual style.", "category": "clothing", "price_stars": 25,
     "effect_type": "xp_bonus_percent", "effect_value": 5, "emoji": "🧢", "rarity": "common"},
    
    {"name": "Шляпа волшебника", "description": "🎩+10% XP always! Magical! LVL10+", "category": "clothing", "price_stars": 50,
     "effect_type": "xp_bonus_percent", "effect_value": 10, "emoji": "🎩", "rarity": "rare",
     "min_level": 10},
    
    {"name": "Корона принца", "description": "👑+15% XP always! Royal! LVL20+", "category": "clothing", "price_stars": 80,
     "effect_type": "xp_bonus_percent", "effect_value": 15, "emoji": "👑", "rarity": "epic",
     "min_level": 20},
    
    {"name": "Императорская корона", "description": "👑✨+25% XP + aura effect! LVL35+", "category": "clothing", "price_stars": 150,
     "effect_type": "xp_bonus_percent", "effect_value": 25, "emoji": "👑✨", "rarity": "legendary",
     "min_level": 35},
    
    {"name": "Нимб", "description": "😇+35% XP + glow effect! LVL50+", "category": "clothing", "price_stars": 300,
     "effect_type": "xp_bonus_percent", "effect_value": 35, "emoji": "😇", "rarity": "legendary",
     "min_level": 50},
    
    # Одежда на тело
    {"name": "Шарфик", "description": "🧣-5% energy loss! Stay warm.", "category": "clothing", "price_stars": 20,
     "effect_type": "energy_save_percent", "effect_value": 5, "emoji": "🧣", "rarity": "common"},
    
    {"name": "Свитер", "description": "🧥-10% energy loss! Cozy! LVL10+", "category": "clothing", "price_stars": 40,
     "effect_type": "energy_save_percent", "effect_value": 10, "emoji": "🧥", "rarity": "rare",
     "min_level": 10},
    
    {"name": "Плащ героя", "description": "🦸-15% energy loss +5% XP! LVL25+", "category": "clothing", "price_stars": 100,
     "effect_type": "hero_cape", "effect_value": 15, "emoji": "🦸", "rarity": "epic",
     "min_level": 25},
    
    {"name": "Мантия архимага", "description": "🧙‍♂️-20% ALL stat loss! LVL40+", "category": "clothing", "price_stars": 200,
     "effect_type": "archmage_robe", "effect_value": 20, "emoji": "🧙‍♂️", "rarity": "legendary",
     "min_level": 40},
    
    # ==========================================
    # АКСЕССУАРЫ (accessory) - special effects while equipped
    # ==========================================
    
    # Ошейники
    {"name": "Простой ошейник", "description": "📿 Cosmetic only. First accessory!", "category": "accessory", "price_stars": 10,
     "effect_type": "cosmetic", "effect_value": 0, "emoji": "📿", "rarity": "common"},
    
    {"name": "Кожаный ошейник", "description": "🔗+2% ALL stats. Stylish!", "category": "accessory", "price_stars": 25,
     "effect_type": "all_stats_bonus", "effect_value": 2, "emoji": "🔗", "rarity": "common"},
    
    {"name": "Серебряный ошейник", "description": "⚪+5% ALL stats! Shiny! LVL10+", "category": "accessory", "price_stars": 50,
     "effect_type": "all_stats_bonus", "effect_value": 5, "emoji": "⚪", "rarity": "rare",
     "min_level": 10},
    
    {"name": "Золотой ошейник", "description": "🥇+10% VPN rewards! LVL20+", "category": "accessory", "price_stars": 100,
     "effect_type": "vpn_bonus_percent", "effect_value": 10, "emoji": "🥇", "rarity": "epic",
     "min_level": 20},
    
    {"name": "Платиновый ошейник", "description": "💎+15% VPN +10% XP! LVL35+", "category": "accessory", "price_stars": 180,
     "effect_type": "platinum_collar", "effect_value": 15, "emoji": "💎", "rarity": "legendary",
     "min_level": 35},
    
    # Амулеты
    {"name": "Амулет удачи", "description": "🍀10% chance for x2 rewards!", "category": "accessory", "price_stars": 60,
     "effect_type": "luck_chance", "effect_value": 10, "emoji": "🍀", "rarity": "rare"},
    
    {"name": "Амулет мудрости", "description": "🦉+10% XP from all actions! LVL15+", "category": "accessory", "price_stars": 80,
     "effect_type": "xp_bonus_percent", "effect_value": 10, "emoji": "🦉", "rarity": "epic",
     "min_level": 15},
    
    {"name": "Амулет бессмертия", "description": "☥Pet CANNOT die from hunger! LVL50+", "category": "accessory", "price_stars": 500,
     "effect_type": "immortality", "effect_value": 1, "emoji": "☥", "rarity": "legendary",
     "min_level": 50},
    
    # Крылья (редкие)
    {"name": "Крылья ангела", "description": "👼+20% XP + wing animation! LVL40+", "category": "accessory", "price_stars": 250,
     "effect_type": "angel_wings", "effect_value": 20, "emoji": "👼", "rarity": "legendary",
     "min_level": 40},
    
    {"name": "Крылья дракона", "description": "🐲+25% ALL bonuses! Ultimate! LVL60+", "category": "accessory", "price_stars": 400,
     "effect_type": "dragon_wings", "effect_value": 25, "emoji": "🐲", "rarity": "legendary",
     "min_level": 60},
    
    # ==========================================
    # VPN ПАКЕТЫ (vpn) - adds hours directly to balance
    # ==========================================
    
    {"name": "VPN 1 день", "description": "🛡️24h VPN access. Instant activation!", "category": "vpn", "price_stars": 15,
     "effect_type": "vpn_hours", "effect_value": 24, "emoji": "🛡️", "rarity": "common"},
    
    {"name": "VPN 3 дня", "description": "🛡️72h VPN access. Weekend pack!", "category": "vpn", "price_stars": 35,
     "effect_type": "vpn_hours", "effect_value": 72, "emoji": "🛡️", "rarity": "common"},
    
    {"name": "VPN Неделя", "description": "🔐168h VPN access. Best weekly deal!", "category": "vpn", "price_stars": 60,
     "effect_type": "vpn_hours", "effect_value": 168, "emoji": "🔐", "rarity": "rare"},
    
    {"name": "VPN 2 недели", "description": "🏰336h VPN access. 14 days!", "category": "vpn", "price_stars": 100,
     "effect_type": "vpn_hours", "effect_value": 336, "emoji": "🏰", "rarity": "epic"},
    
    {"name": "VPN Месяц", "description": "🚀720h VPN access. Full month!", "category": "vpn", "price_stars": 180,
     "effect_type": "vpn_hours", "effect_value": 720, "emoji": "🚀", "rarity": "legendary"},
    
    {"name": "VPN 3 месяца", "description": "🌟2160h VPN + 17% discount! Best value!", "category": "vpn", "price_stars": 450,
     "effect_type": "vpn_hours", "effect_value": 2160, "emoji": "🌟🚀", "rarity": "legendary"},
]

# Уникальные эффекты
SPECIAL_EFFECTS = {
    "divine_restore": "Полное восстановление + 1ч буст всех статов",
    "zeus_bolt": "Максимум энергии + удвоенная скорость действий",
    "rainbow_happiness": "Радужный визуальный эффект вокруг питомца",
    "happiness_lock": "Счастье не падает в течение действия буста",
    "hero_cape": "Плащ с анимацией развевания",
    "archmage_robe": "Магические частицы вокруг питомца",
    "angel_wings": "Белые светящиеся крылья",
    "dragon_wings": "Огненные крылья дракона",
    "immortality": "Золотая аура - питомец не может умереть от голода",
}

def get_evolution_for_level(level: int) -> dict:
    """Получить эволюцию для данного уровня"""
    current_evo = None
    for evo_level, evo_data in sorted(PET_EVOLUTIONS.items()):
        if level >= evo_level:
            current_evo = {"level": evo_level, **evo_data}
    return current_evo

def get_next_evolution(level: int) -> dict:
    """Получить следующую эволюцию"""
    for evo_level, evo_data in sorted(PET_EVOLUTIONS.items()):
        if evo_level > level:
            return {"level": evo_level, **evo_data}
    return None

def get_level_reward(level: int) -> dict:
    """Получить награду за достижение уровня"""
    return LEVEL_REWARDS.get(level)

def get_available_items_for_level(level: int) -> list:
    """Получить предметы доступные для данного уровня"""
    return [
        item for item in EXTENDED_SHOP_ITEMS
        if item.get("min_level", 0) <= level
    ]
