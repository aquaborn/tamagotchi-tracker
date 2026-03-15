"""
Система прогрессии питомца - эволюция, уровни, бонусы
"""

# === ЭВОЛЮЦИИ ПИТОМЦЕВ ПО ТИПАМ ===
# Уникальные линейки эволюции для каждого типа питомца

PET_EVOLUTIONS_BY_TYPE = {
    "kitty": {
        1: {"name": "Малыш-котёнок", "emoji": "🐱", "description": "Маленький милый котёнок"},
        5: {"name": "Котёнок", "emoji": "🐱", "description": "Игривый пушистик"},
        10: {"name": "Кот", "emoji": "😺", "description": "Взрослый умный кот"},
        20: {"name": "Мудрый кот", "emoji": "😸", "description": "Опытный кот"},
        35: {"name": "Кот-мастер", "emoji": "😻", "description": "Мастер кошачьих дел"},
        50: {"name": "Лев", "emoji": "🦁", "description": "Легендарный лев!"},
        75: {"name": "Саблезубый", "emoji": "🐅", "description": "Мифический хищник"},
        100: {"name": "Божественный кот", "emoji": "✨🐱", "description": "Божественное существо"}
    },
    "puppy": {
        1: {"name": "Щеночек", "emoji": "🐶", "description": "Маленький щенок"},
        5: {"name": "Пёсик", "emoji": "🐶", "description": "Игривый пёсик"},
        10: {"name": "Собака", "emoji": "🐕", "description": "Верный друг"},
        20: {"name": "Овчарка", "emoji": "🦮", "description": "Умная овчарка"},
        35: {"name": "Вожак", "emoji": "🐺", "description": "Вожак стаи"},
        50: {"name": "Волк", "emoji": "🐺", "description": "Легендарный волк!"},
        75: {"name": "Диреволк", "emoji": "🐺✨", "description": "Мифический диреволк"},
        100: {"name": "Божественный пёс", "emoji": "✨🐕", "description": "Божественный!"}
    },
    "bunny": {
        1: {"name": "Крольчонок", "emoji": "🐰", "description": "Пушистый крольчонок"},
        5: {"name": "Зайчик", "emoji": "🐰", "description": "Быстрый зайчик"},
        10: {"name": "Заяц", "emoji": "🐇", "description": "Взрослый заяц"},
        20: {"name": "Белый заяц", "emoji": "🐇", "description": "Мудрый белый заяц"},
        35: {"name": "Кролик-волшебник", "emoji": "🐇✨", "description": "Магический кролик"},
        50: {"name": "Лунный заяц", "emoji": "🌙🐇", "description": "Легендарный!"},
        75: {"name": "Небесный заяц", "emoji": "☁️🐇", "description": "Мифический"},
        100: {"name": "Божественный кролик", "emoji": "✨🐰", "description": "Божественный!"}
    },
    "frog": {
        1: {"name": "Головастик", "emoji": "🐣", "description": "Маленький головастик"},
        5: {"name": "Лягушонок", "emoji": "🐸", "description": "Малыш-лягушонок"},
        10: {"name": "Лягушка", "emoji": "🐸", "description": "Весёлая лягушка"},
        20: {"name": "Жаба", "emoji": "🐸", "description": "Мудрая жаба"},
        35: {"name": "Царевна-лягушка", "emoji": "👸🐸", "description": "Королевская особа"},
        50: {"name": "Лягушка-принц", "emoji": "🤴🐸", "description": "Легендарный!"},
        75: {"name": "Древняя жаба", "emoji": "🐸🌿", "description": "Мифическая"},
        100: {"name": "Божественная лягушка", "emoji": "✨🐸", "description": "Божественная!"}
    },
    "hamster": {
        1: {"name": "Хомячок", "emoji": "🐹", "description": "Крошечный хомячок"},
        5: {"name": "Хомяк", "emoji": "🐹", "description": "Пушистый хомяк"},
        10: {"name": "Толстый хомяк", "emoji": "🐹", "description": "Хомяк с полными щеками"},
        20: {"name": "Золотой хомяк", "emoji": "🐹✨", "description": "Золотистый мех"},
        35: {"name": "Хомяк-босс", "emoji": "🐹👑", "description": "Главный хомяк"},
        50: {"name": "Король хомяков", "emoji": "👑🐹", "description": "Легендарный!"},
        75: {"name": "Хомяк-титан", "emoji": "🐹💪", "description": "Мифический"},
        100: {"name": "Божественный хомяк", "emoji": "✨🐹", "description": "Божественный!"}
    },
    "bear_cub": {
        1: {"name": "Медвежонок", "emoji": "🐻", "description": "Милый медвежонок"},
        5: {"name": "Мишка", "emoji": "🐻", "description": "Пушистый мишка"},
        10: {"name": "Медведь", "emoji": "🐻", "description": "Взрослый медведь"},
        20: {"name": "Бурый медведь", "emoji": "🐻", "description": "Сильный медведь"},
        35: {"name": "Гризли", "emoji": "🐻💪", "description": "Могучий гризли"},
        50: {"name": "Полярный медведь", "emoji": "🐻‍❄️", "description": "Легендарный!"},
        75: {"name": "Пещерный медведь", "emoji": "🐻🗿", "description": "Мифический"},
        100: {"name": "Божественный медведь", "emoji": "✨🐻", "description": "Божественный!"}
    },
    "fox": {
        1: {"name": "Лисёнок", "emoji": "🦊", "description": "Малыш-лисёнок"},
        5: {"name": "Лисичка", "emoji": "🦊", "description": "Хитрая лисичка"},
        10: {"name": "Лиса", "emoji": "🦊", "description": "Рыжая лиса"},
        20: {"name": "Чернобурая лиса", "emoji": "🦊", "description": "Редкая окраска"},
        35: {"name": "Полярная лиса", "emoji": "🦊❄️", "description": "Белоснежная"},
        50: {"name": "Девятихвостая", "emoji": "🦊✨", "description": "Легендарная!"},
        75: {"name": "Кицунэ", "emoji": "🦊🔥", "description": "Мифическая лиса"},
        100: {"name": "Божественная лиса", "emoji": "✨🦊", "description": "Божественная!"}
    },
    "panda": {
        1: {"name": "Пандёнок", "emoji": "🐼", "description": "Малыш-панда"},
        5: {"name": "Панда", "emoji": "🐼", "description": "Милая панда"},
        10: {"name": "Большая панда", "emoji": "🐼", "description": "Ленивая панда"},
        20: {"name": "Кунг-фу панда", "emoji": "🐼🥋", "description": "Воин панда"},
        35: {"name": "Мастер панда", "emoji": "🐼🥋", "description": "Мастер боевых искусств"},
        50: {"name": "Инь-Янь панда", "emoji": "☯️🐼", "description": "Легендарная!"},
        75: {"name": "Небесная панда", "emoji": "🐼☁️", "description": "Мифическая"},
        100: {"name": "Божественная панда", "emoji": "✨🐼", "description": "Божественная!"}
    },
    "chick": {
        1: {"name": "Цыплёнок", "emoji": "🐥", "description": "Маленький цыплёнок"},
        5: {"name": "Птенчик", "emoji": "🐤", "description": "Жёлтый птенчик"},
        10: {"name": "Курочка", "emoji": "🐔", "description": "Взрослая курочка"},
        20: {"name": "Петух", "emoji": "🐓", "description": "Гордый петух"},
        35: {"name": "Золотой петушок", "emoji": "🐓✨", "description": "Сказочный"},
        50: {"name": "Феникс", "emoji": "🔥🦅", "description": "Легендарный феникс!"},
        75: {"name": "Огненный феникс", "emoji": "🔥🦅✨", "description": "Мифический"},
        100: {"name": "Божественный феникс", "emoji": "✨🦅", "description": "Божественный!"}
    },
    "hedgehog": {
        1: {"name": "Ёжик", "emoji": "🦔", "description": "Маленький ёжик"},
        5: {"name": "Ёж", "emoji": "🦔", "description": "Колючий ёж"},
        10: {"name": "Большой ёж", "emoji": "🦔", "description": "Взрослый ёж"},
        20: {"name": "Золотой ёж", "emoji": "🦔✨", "description": "Редкий окрас"},
        35: {"name": "Соник", "emoji": "🦔💨", "description": "Быстрый как Соник"},
        50: {"name": "Супер Соник", "emoji": "🦔⭐", "description": "Легендарный!"},
        75: {"name": "Гипер Соник", "emoji": "🦔💎", "description": "Мифический"},
        100: {"name": "Божественный ёж", "emoji": "✨🦔", "description": "Божественный!"}
    },
}

# Default evolutions for unknown pet types
DEFAULT_EVOLUTIONS = {
    1: {"name": "Малыш", "emoji": "🐣", "description": "Маленький питомец"},
    5: {"name": "Подросток", "emoji": "🐥", "description": "Растёт!"},
    10: {"name": "Взрослый", "emoji": "🦾", "description": "Взрослый питомец"},
    20: {"name": "Мудрый", "emoji": "🦾✨", "description": "Опытный"},
    35: {"name": "Мастер", "emoji": "🌟", "description": "Мастер"},
    50: {"name": "Легенда", "emoji": "🌟✨", "description": "Легендарный!"},
    75: {"name": "Мифический", "emoji": "🐉", "description": "Мифический"},
    100: {"name": "Божественный", "emoji": "✨", "description": "Божественный!"}
}

# Keep old PET_EVOLUTIONS for backwards compatibility
PET_EVOLUTIONS = DEFAULT_EVOLUTIONS

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
    # ИГРУШКИ (toy) - boost happiness when equipped
    # ==========================================
    
    {"name": "Мячик", "description": "⚽+10% happiness gain! Play time!", "category": "toy", "price_stars": 15,
     "effect_type": "happiness_bonus", "effect_value": 10, "emoji": "⚽", "rarity": "common"},
    
    {"name": "Клубок пряжи", "description": "🧶+15% happiness gain! Cat favorite!", "category": "toy", "price_stars": 20,
     "effect_type": "happiness_bonus", "effect_value": 15, "emoji": "🧶", "rarity": "common"},
    
    {"name": "Плюшевый мишка", "description": "🧸+20% happiness gain! Cuddle buddy!", "category": "toy", "price_stars": 30,
     "effect_type": "happiness_bonus", "effect_value": 20, "emoji": "🧸", "rarity": "rare"},
    
    {"name": "Косточка", "description": "🦴+25% happiness gain! Dog favorite! LVL10+", "category": "toy", "price_stars": 40,
     "effect_type": "happiness_bonus", "effect_value": 25, "emoji": "🦴", "rarity": "rare",
     "min_level": 10},
    
    {"name": "Мышка-игрушка", "description": "🐭+30% happiness gain! Hunt time! LVL15+", "category": "toy", "price_stars": 50,
     "effect_type": "happiness_bonus", "effect_value": 30, "emoji": "🐭", "rarity": "epic",
     "min_level": 15},
    
    {"name": "Пёрышко", "description": "🪶+35% happiness gain! Bird play! LVL20+", "category": "toy", "price_stars": 70,
     "effect_type": "happiness_bonus", "effect_value": 35, "emoji": "🪶", "rarity": "epic",
     "min_level": 20},
    
    {"name": "Баскетбольный мяч", "description": "🏀+40% happiness +5% XP! Sport star! LVL30+", "category": "toy", "price_stars": 100,
     "effect_type": "sport_ball", "effect_value": 40, "emoji": "🏀", "rarity": "legendary",
     "min_level": 30},
    
    {"name": "Золотой мяч", "description": "🥎+50% happiness +10% XP! Champion! LVL50+", "category": "toy", "price_stars": 200,
     "effect_type": "golden_ball", "effect_value": 50, "emoji": "🥎", "rarity": "legendary",
     "min_level": 50},
    
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

def get_evolutions_for_pet(pet_type: str) -> dict:
    """Get evolution tree for specific pet type"""
    return PET_EVOLUTIONS_BY_TYPE.get(pet_type, DEFAULT_EVOLUTIONS)

def get_evolution_for_level(level: int, pet_type: str = None) -> dict:
    """Получить эволюцию для данного уровня"""
    evolutions = get_evolutions_for_pet(pet_type) if pet_type else PET_EVOLUTIONS
    current_evo = None
    for evo_level, evo_data in sorted(evolutions.items()):
        if level >= evo_level:
            current_evo = {"level": evo_level, **evo_data}
    return current_evo

def get_next_evolution(level: int, pet_type: str = None) -> dict:
    """Получить следующую эволюцию"""
    evolutions = get_evolutions_for_pet(pet_type) if pet_type else PET_EVOLUTIONS
    for evo_level, evo_data in sorted(evolutions.items()):
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
