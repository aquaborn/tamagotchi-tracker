import asyncio
import json
import secrets
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import aiohttp

logger = logging.getLogger(__name__)


# Конфигурация VPN сервера
VPN_SERVER_IP = "185.9.27.123"
VPN_SERVER_SSH_USER = "root"
VPN_SERVER_SSH_KEY = "/app/ssh_key"  # Путь к SSH ключу в контейнере


# Награды в часах
REWARDS = {
    "referral": 48,           # 2 дня за реферала
    "level_up": 48,           # 2 дня за уровень
    "happy_pet_daily": 24,    # 1 день за довольного питомца
    "streak_7": 72,           # 3 дня за 7-дневный стрик
    "streak_30": 168,         # 7 дней за 30-дневный стрик
    "first_feed": 12,         # 12 часов за первое кормление
    "first_play": 12,         # 12 часов за первую игру
    "level_5": 48,            # 2 дня за 5 уровень
    "level_10": 96,           # 4 дня за 10 уровень
}

# Опыт за действия
XP_REWARDS = {
    "feed": 10,
    "play": 15,
    "sleep": 5,
    "wake": 0,
    "bath": 12,
    "heal": 20,
    "discipline": 15,
    "light_on": 0,
    "light_off": 0,
    "daily_login": 50,
    "referral": 100,
}

# Уровни (опыт необходимый)
def get_level_xp_required(level: int) -> int:
    return level * 100 + (level - 1) * 50


def generate_referral_code() -> str:
    """Генерирует уникальный реферальный код"""
    return secrets.token_urlsafe(8)[:12].upper()


async def generate_xray_config(user_id: int, hours: int) -> Optional[str]:
    """
    Генерирует конфиг Xray для пользователя.
    В production - подключается к серверу через API или SSH.
    """
    try:
        # UUID для клиента
        client_uuid = secrets.token_hex(16)
        client_uuid = f"{client_uuid[:8]}-{client_uuid[8:12]}-{client_uuid[12:16]}-{client_uuid[16:20]}-{client_uuid[20:]}"
        
        # Генерируем конфиг для клиента
        config = {
            "dns": {
                "servers": ["1.1.1.1", "8.8.8.8"]
            },
            "inbounds": [
                {
                    "port": 10808,
                    "protocol": "socks",
                    "settings": {
                        "udp": True
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": VPN_SERVER_IP,
                                "port": 443,
                                "users": [
                                    {
                                        "id": client_uuid,
                                        "encryption": "none",
                                        "flow": "xtls-rprx-vision"
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "fingerprint": "chrome",
                            "serverName": "www.google.com",
                            "publicKey": "YOUR_PUBLIC_KEY_HERE",  # Заменить на реальный
                            "shortId": ""
                        }
                    }
                }
            ]
        }
        
        # В production: здесь нужно добавить пользователя на сервер
        # await add_user_to_xray_server(client_uuid, user_id, hours)
        
        return json.dumps(config, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating Xray config: {e}")
        return None


async def generate_amnezia_config(user_id: int, hours: int) -> Optional[str]:
    """
    Генерирует конфиг для Amnezia VPN.
    Формат: vpn://... URI
    """
    try:
        # Генерируем простой конфиг в формате Amnezia
        client_id = secrets.token_hex(8)
        
        # Amnezia config URI
        config = {
            "containers": [
                {
                    "container": "amnezia-xray",
                    "protocol": "xray",
                    "server": VPN_SERVER_IP,
                    "port": 443,
                    "client_id": client_id,
                    "user_id": user_id,
                    "expires_hours": hours
                }
            ],
            "description": f"TamaGuardian VPN - {hours}h",
            "dns1": "1.1.1.1",
            "dns2": "8.8.8.8"
        }
        
        return json.dumps(config)
        
    except Exception as e:
        logger.error(f"Error generating Amnezia config: {e}")
        return None


def calculate_new_level(current_xp: int, added_xp: int, current_level: int) -> tuple[int, int, bool]:
    """
    Рассчитывает новый уровень.
    Возвращает: (новый_опыт, новый_уровень, был_ли_левелап)
    """
    new_xp = current_xp + added_xp
    new_level = current_level
    leveled_up = False
    
    while new_xp >= get_level_xp_required(new_level):
        new_xp -= get_level_xp_required(new_level)
        new_level += 1
        leveled_up = True
    
    return new_xp, new_level, leveled_up


def check_streak(last_activity: Optional[datetime], current_time: datetime) -> tuple[int, bool]:
    """
    Проверяет и обновляет стрик.
    Возвращает: (новый_стрик, получил_ли_награду_за_стрик)
    """
    if last_activity is None:
        return 1, False
    
    # Приводим к UTC
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    # Разница в днях
    days_diff = (current_time.date() - last_activity.date()).days
    
    if days_diff == 0:
        # Тот же день
        return -1, False  # -1 означает не обновлять
    elif days_diff == 1:
        # Следующий день - стрик продолжается
        return -1, True  # Увеличить на 1
    else:
        # Пропустил день - стрик сбрасывается
        return 1, False


# Достижения
ACHIEVEMENTS = {
    "first_feed": {"name": "Первое кормление", "reward_hours": 12},
    "first_play": {"name": "Первая игра", "reward_hours": 12},
    "first_sleep": {"name": "Первый сон", "reward_hours": 12},
    "streak_3": {"name": "3 дня подряд", "reward_hours": 24},
    "streak_7": {"name": "Неделя заботы", "reward_hours": 72},
    "streak_30": {"name": "Месяц заботы", "reward_hours": 168},
    "level_5": {"name": "Уровень 5", "reward_hours": 48},
    "level_10": {"name": "Уровень 10", "reward_hours": 96},
    "level_25": {"name": "Уровень 25", "reward_hours": 168},
    "referral_1": {"name": "Первый друг", "reward_hours": 48},
    "referral_5": {"name": "Компания друзей", "reward_hours": 120},
    "referral_10": {"name": "Популярный", "reward_hours": 240},
    "happy_pet_3": {"name": "Заботливый хозяин", "reward_hours": 36},
    "happy_pet_7": {"name": "Лучший друг питомца", "reward_hours": 72},
}
