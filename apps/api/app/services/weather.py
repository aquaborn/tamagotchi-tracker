"""
Weather System - погода и времена года влияют на питомца
"""
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

# Времена года
SEASONS = {
    "winter": {
        "name": "Зима",
        "emoji": "❄️",
        "months": [12, 1, 2],
        "base_temp": -10,
        "effects": {
            "energy_drain": 1.15,   # +15% потеря энергии (холодно)
            "hunger_drain": 1.20,   # +20% голод (нужно больше еды)
        },
        "clothing_protection": ["🧥", "🧣", "🧤"],  # Защитная одежда
    },
    "spring": {
        "name": "Весна",
        "emoji": "🌸",
        "months": [3, 4, 5],
        "base_temp": 10,
        "effects": {},
        "clothing_protection": [],
    },
    "summer": {
        "name": "Лето",
        "emoji": "☀️",
        "months": [6, 7, 8],
        "base_temp": 25,
        "effects": {},
        "clothing_protection": [],
    },
    "autumn": {
        "name": "Осень",
        "emoji": "🍂",
        "months": [9, 10, 11],
        "base_temp": 8,
        "effects": {
            "happiness_drain": 1.10,  # +10% грусть
        },
        "clothing_protection": ["🧣"],
    }
}

# Типы погоды
WEATHER_TYPES = {
    "sunny": {
        "name": "Солнечно",
        "emoji": "☀️",
        "description": "Отличная погода!",
        "effects": {},  # Нет эффектов
        "severity": 0,
        "animation": "sunny"
    },
    "cloudy": {
        "name": "Облачно",
        "emoji": "⛅",
        "description": "Небольшая облачность",
        "effects": {},
        "severity": 0,
        "animation": "cloudy"
    },
    "rain": {
        "name": "Дождь",
        "emoji": "🌧️",
        "description": "Идёт дождь, питомец мокнет!",
        "effects": {
            "energy_drain": 1.3,      # +30% потеря энергии
            "happiness_drain": 1.2,   # +20% потеря счастья
            "hygiene_boost": 1.1      # +10% к чистоте (дождь моет)
        },
        "severity": 1,
        "animation": "rain"
    },
    "storm": {
        "name": "Гроза",
        "emoji": "⛈️",
        "description": "Сильная гроза! Питомец напуган!",
        "effects": {
            "energy_drain": 1.5,
            "happiness_drain": 1.4,
            "hunger_drain": 1.2
        },
        "severity": 2,
        "animation": "storm"
    },
    "snow": {
        "name": "Снег",
        "emoji": "❄️",
        "description": "Идёт снег, холодно!",
        "effects": {
            "energy_drain": 1.4,
            "hunger_drain": 1.3       # Больше еды нужно чтобы согреться
        },
        "severity": 1,
        "animation": "snow"
    },
    "blizzard": {
        "name": "Метель",
        "emoji": "🌨️",
        "description": "Сильная метель! Очень холодно!",
        "effects": {
            "energy_drain": 1.6,
            "hunger_drain": 1.5,
            "happiness_drain": 1.3
        },
        "severity": 2,
        "animation": "blizzard"
    },
    "hot": {
        "name": "Жара",
        "emoji": "🔥",
        "description": "Очень жарко!",
        "effects": {
            "energy_drain": 1.3,
            "hunger_drain": 1.2
        },
        "severity": 1,
        "animation": "hot"
    }
}

# Храним текущую погоду и время следующей смены
_current_weather = None
_weather_change_time = None

# Уровни укрытий (будок)
SHELTER_LEVELS = {
    0: {
        "name": "Нет укрытия",
        "emoji": "🚫",
        "protection": 0,
        "price": 0,
        "visual": None
    },
    1: {
        "name": "Картонная коробка",
        "emoji": "📦",
        "protection": 0.3,  # 30% защита
        "price": 50,
        "visual": "cardboard",
        "description": "Простая коробка. Хоть что-то!"
    },
    2: {
        "name": "Деревянная будка",
        "emoji": "🏠",
        "protection": 0.6,  # 60% защита
        "price": 150,
        "visual": "wooden",
        "description": "Уютная деревянная будка"
    },
    3: {
        "name": "Каменный домик",
        "emoji": "🏰",
        "protection": 0.85,
        "price": 400,
        "visual": "stone",
        "description": "Надёжный каменный дом"
    },
    4: {
        "name": "Роскошный особняк",
        "emoji": "🏯",
        "protection": 1.0,  # 100% защита
        "price": 1000,
        "visual": "mansion",
        "description": "Роскошный особняк с отоплением!",
        "bonus": {"xp_multiplier": 1.05}
    },
    5: {
        "name": "Небесный дворец",
        "emoji": "✨🏯",
        "protection": 1.0,
        "price": 2500,
        "visual": "palace",
        "description": "Магический дворец в облаках!",
        "bonus": {"xp_multiplier": 1.15, "all_stats_slow": 0.9}
    }
}

def get_current_season() -> dict:
    """Получить текущее время года"""
    month = datetime.now(timezone.utc).month
    for season_id, season in SEASONS.items():
        if month in season["months"]:
            return {"id": season_id, **season}
    return {"id": "summer", **SEASONS["summer"]}

def get_current_weather() -> dict:
    """
    Получить текущую погоду.
    Погода меняется рандомно (15-90 минут).
    """
    global _current_weather, _weather_change_time
    
    now = datetime.now(timezone.utc)
    
    # Проверяем нужно ли менять погоду
    if _current_weather is None or _weather_change_time is None or now >= _weather_change_time:
        # Генерируем новую погоду
        season = get_current_season()
        
        # Веса для разных типов погоды
        weather_weights = {
            "sunny": 30,
            "cloudy": 25,
            "rain": 18,
            "storm": 6,
            "snow": 12,
            "blizzard": 4,
            "hot": 5
        }
        
        # Сезонные модификаторы
        if season["id"] == "winter":
            weather_weights["snow"] *= 4
            weather_weights["blizzard"] *= 3
            weather_weights["hot"] = 0
            weather_weights["sunny"] = 10
        elif season["id"] == "summer":
            weather_weights["hot"] *= 4
            weather_weights["sunny"] *= 2
            weather_weights["snow"] = 0
            weather_weights["blizzard"] = 0
        elif season["id"] == "autumn":
            weather_weights["rain"] *= 3
            weather_weights["cloudy"] *= 2
            weather_weights["snow"] = 5
        elif season["id"] == "spring":
            weather_weights["rain"] *= 2
            weather_weights["sunny"] *= 1.5
        
        # Выбираем погоду
        choices = []
        for weather_type, weight in weather_weights.items():
            choices.extend([weather_type] * int(weight))
        
        selected = random.choice(choices)
        weather = WEATHER_TYPES[selected].copy()
        weather["type"] = selected
        
        # Рандомная длительность: 15-90 минут
        # Плохая погода длится меньше, хорошая - дольше
        if weather.get("severity", 0) >= 2:
            duration_minutes = random.randint(15, 40)  # Катастрофа - коротко
        elif weather.get("severity", 0) == 1:
            duration_minutes = random.randint(30, 60)  # Плохая погода
        else:
            duration_minutes = random.randint(45, 90)  # Хорошая погода
        
        _current_weather = weather
        _weather_change_time = now + timedelta(minutes=duration_minutes)
    
    # Вычисляем минуты до смены
    time_left = (_weather_change_time - now).total_seconds() / 60
    
    result = _current_weather.copy()
    result["next_change_minutes"] = max(1, int(time_left))
    result["season"] = get_current_season()
    
    return result

def get_shelter_info(level: int) -> dict:
    """Получить информацию об укрытии"""
    return SHELTER_LEVELS.get(level, SHELTER_LEVELS[0])

def get_next_shelter_upgrade(current_level: int) -> Optional[dict]:
    """Получить информацию о следующем апгрейде"""
    next_level = current_level + 1
    if next_level in SHELTER_LEVELS:
        shelter = SHELTER_LEVELS[next_level].copy()
        shelter["level"] = next_level
        return shelter
    return None

def calculate_weather_effects(weather: dict, shelter_level: int, equipped_clothing: list = None) -> dict:
    """
    Рассчитать эффекты погоды и сезона с учётом укрытия и одежды.
    """
    shelter = get_shelter_info(shelter_level)
    protection = shelter["protection"]
    season = get_current_season()
    equipped_clothing = equipped_clothing or []
    
    # Объединяем эффекты погоды и сезона
    combined_effects = {}
    
    # Эффекты сезона
    for effect, value in season.get("effects", {}).items():
        combined_effects[effect] = value
    
    # Эффекты погоды (умножаем)
    for effect, value in weather.get("effects", {}).items():
        if effect in combined_effects:
            combined_effects[effect] *= value
        else:
            combined_effects[effect] = value
    
    if not combined_effects:
        return {"modified": False, "multipliers": {}, "hiding_in_shelter": False, "clothing_helps": False}
    
    # Проверяем защитную одежду для сезона
    clothing_protection = 0
    protective_clothing = season.get("clothing_protection", [])
    for emoji in protective_clothing:
        if emoji in equipped_clothing:
            clothing_protection += 0.25  # Каждый предмет даёт 25% защиты
    clothing_protection = min(clothing_protection, 0.75)  # Макс 75% от одежды
    
    # Если укрытие защищает на 100%
    if protection >= 1.0:
        return {
            "modified": False, 
            "multipliers": {},
            "hiding_in_shelter": weather.get("severity", 0) > 0,
            "clothing_helps": False
        }
    
    # Суммарная защита
    total_protection = min(protection + clothing_protection, 0.95)
    
    # Применяем защиту
    modified_effects = {}
    for effect, value in combined_effects.items():
        if value > 1.0:  # Только для негативных эффектов
            reduction = (value - 1.0) * (1 - total_protection)
            modified_effects[effect] = 1.0 + reduction
        else:
            modified_effects[effect] = value
    
    return {
        "modified": True,
        "multipliers": modified_effects,
        "hiding_in_shelter": protection > 0 and weather.get("severity", 0) > 0,
        "clothing_helps": clothing_protection > 0,
        "season_id": season["id"],
        "season_name": season["name"]
    }

def should_pet_hide(weather: dict, shelter_level: int) -> bool:
    """Должен ли питомец прятаться в укрытие"""
    if shelter_level == 0:
        return False
    return weather.get("severity", 0) > 0

def get_all_shelter_levels() -> list:
    """Получить все уровни укрытий для магазина"""
    return [
        {"level": level, **data}
        for level, data in SHELTER_LEVELS.items()
        if level > 0  # Исключаем "нет укрытия"
    ]
