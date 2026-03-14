"""
Star Roulette - Ежедневная лотерея звёзд
"""
import random
import hashlib
import json
import os
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
import logging

logger = logging.getLogger(__name__)

# Файл для сохранения пула рулетки (персистентность)
ROULETTE_FILE = '/tmp/roulette_pools.json'

# Lock для потокобезопасной записи
_file_lock = threading.Lock()

# Конфигурация рулетки
ROULETTE_CONFIG = {
    "min_bet": 10,           # Минимальная ставка
    "max_bet": 500,          # Максимальная ставка
    "draw_hour_utc": 20,     # Час розыгрыша (20:00 UTC = 23:00 МСК)
    "admin_ids": [84481976], # Админы для уведомлений
}

# Твисты в зависимости от банка
POOL_TWISTS = {
    100: {
        "name": "Мини-банк",
        "emoji": "🎲",
        "description": "Базовый розыгрыш",
        "winner_count": 1,
        "bonus": None
    },
    500: {
        "name": "Средний банк",
        "emoji": "🎰",
        "description": "Шанс x1.5 для топ ставки!",
        "winner_count": 1,
        "bonus": {"top_bet_multiplier": 1.5}  # Топ ставщик получает x1.5 шанс
    },
    1000: {
        "name": "Большой банк",
        "emoji": "💰",
        "description": "2 победителя! 70/30 split",
        "winner_count": 2,
        "split": [0.7, 0.3],
        "bonus": {"top_bet_multiplier": 1.5}
    },
    2500: {
        "name": "Мега-банк",
        "emoji": "👑",
        "description": "3 победителя! 60/25/15 split + бонус VPN",
        "winner_count": 3,
        "split": [0.6, 0.25, 0.15],
        "bonus": {
            "top_bet_multiplier": 2.0,
            "vpn_hours": 24  # Бонус VPN для главного победителя
        }
    },
    5000: {
        "name": "ДЖЕКПОТ",
        "emoji": "🌟",
        "description": "JACKPOT! 3 победителя + VPN месяц главному!",
        "winner_count": 3,
        "split": [0.6, 0.25, 0.15],
        "bonus": {
            "top_bet_multiplier": 2.5,
            "vpn_hours": 720  # Месяц VPN!
        }
    }
}

def get_current_twist(pool_total: int) -> dict:
    """Получить твист для текущего размера банка"""
    current_twist = POOL_TWISTS[100]  # Дефолт
    for threshold, twist in sorted(POOL_TWISTS.items()):
        if pool_total >= threshold:
            current_twist = twist
    return current_twist

def get_today_roulette_id() -> str:
    """Уникальный ID розыгрыша на сегодня"""
    today = datetime.now(timezone.utc).date()
    return f"roulette_{today.isoformat()}"

def get_next_draw_time() -> datetime:
    """Время следующего розыгрыша"""
    now = datetime.now(timezone.utc)
    draw_time = now.replace(
        hour=ROULETTE_CONFIG["draw_hour_utc"],
        minute=0,
        second=0,
        microsecond=0
    )
    
    # Если уже прошло время розыгрыша сегодня, следующий завтра
    if now >= draw_time:
        draw_time += timedelta(days=1)
    
    return draw_time

def generate_provably_fair_seed(roulette_id: str, server_seed: str = "TamaGuardian2026") -> str:
    """
    Генерация честного seed для розыгрыша.
    Можно показать участникам для проверки честности.
    """
    combined = f"{roulette_id}:{server_seed}:{datetime.now(timezone.utc).date()}"
    return hashlib.sha256(combined.encode()).hexdigest()

def select_winners(
    participants: List[Dict],  # [{"user_id": 123, "bet": 50, "username": "xxx"}, ...]
    pool_total: int,
    seed: str
) -> List[Dict]:
    """
    Выбор победителей с учётом размера ставок.
    Больше ставка = больше шанс, но всё честно.
    """
    if not participants:
        return []
    
    twist = get_current_twist(pool_total)
    winner_count = twist["winner_count"]
    top_bet_multiplier = twist.get("bonus", {}).get("top_bet_multiplier", 1.0) if twist.get("bonus") else 1.0
    
    # Находим максимальную ставку
    max_bet = max(p["bet"] for p in participants)
    
    # Создаём взвешенный список для рандома
    # Шанс пропорционален ставке, топ ставщики получают бонус
    weighted_pool = []
    for p in participants:
        weight = p["bet"]
        if p["bet"] == max_bet and top_bet_multiplier > 1.0:
            weight = int(weight * top_bet_multiplier)
        
        weighted_pool.extend([p] * weight)
    
    # Используем seed для рандома (provably fair)
    random.seed(seed)
    
    winners = []
    remaining = weighted_pool.copy()
    
    for i in range(min(winner_count, len(participants))):
        if not remaining:
            break
        
        winner = random.choice(remaining)
        winners.append(winner)
        
        # Убираем победителя из пула (не может выиграть дважды)
        remaining = [p for p in remaining if p["user_id"] != winner["user_id"]]
    
    random.seed()  # Сбрасываем seed
    
    # Рассчитываем выигрыши
    split = twist.get("split", [1.0])
    for i, winner in enumerate(winners):
        split_percent = split[i] if i < len(split) else split[-1]
        winner["prize"] = int(pool_total * split_percent)
        winner["place"] = i + 1
        winner["vpn_bonus"] = twist.get("bonus", {}).get("vpn_hours", 0) if i == 0 else 0
    
    return winners

def format_winner_notification(winners: List[Dict], pool_total: int, roulette_id: str) -> str:
    """Форматирование уведомления для админа"""
    twist = get_current_twist(pool_total)
    
    msg = f"""
🎰 **STAR ROULETTE РЕЗУЛЬТАТЫ** 🎰
━━━━━━━━━━━━━━━━━━━━━━
📅 Розыгрыш: {roulette_id}
💰 Банк: {pool_total} ⭐ ({twist['name']})
👥 Участников: определяется
━━━━━━━━━━━━━━━━━━━━━━

🏆 **ПОБЕДИТЕЛИ:**
"""
    
    for w in winners:
        place_emoji = ["🥇", "🥈", "🥉"][w["place"]-1] if w["place"] <= 3 else "🎖️"
        vpn_text = f" + {w['vpn_bonus']}h VPN!" if w.get("vpn_bonus", 0) > 0 else ""
        msg += f"""
{place_emoji} **{w['place']} место:** @{w.get('username', 'user')} (ID: `{w['user_id']}`)
   💫 Выигрыш: **{w['prize']} ⭐**{vpn_text}
   📋 Команда: `/give_stars {w['user_id']} {w['prize']}`
"""
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    return msg

def format_winner_share_text(winner: Dict, pool_total: int) -> str:
    """Текст для автошейра победителем"""
    return f"""🎉 Я ВЫИГРАЛ В STAR ROULETTE! 🎉

💰 Мой выигрыш: {winner['prize']} ⭐
🏆 Место: #{winner['place']}
👥 Банк был: {pool_total} ⭐

Участвуй в ежедневной лотерее @tama_guardian_bot! 🎰"""

# Структура для хранения - сохраняется в файл для персистентности
class RoulettePool:
    """Хранилище с персистентностью в файл"""
    _pools = {}  # {roulette_id: {"participants": [], "total": 0, "drawn": False}}
    _loaded = False
    
    @classmethod
    def _load_from_file(cls):
        """Load pools from file on startup - ТОЛЬКО РАЗ!"""
        if cls._loaded:
            return  # Уже загружено
        cls._loaded = True
        try:
            if os.path.exists(ROULETTE_FILE):
                with open(ROULETTE_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back
                    for pool_id, pool in data.items():
                        pool['created_at'] = datetime.fromisoformat(pool['created_at']) if pool.get('created_at') else datetime.now(timezone.utc)
                        for p in pool.get('participants', []):
                            if p.get('joined_at'):
                                p['joined_at'] = datetime.fromisoformat(p['joined_at'])
                    cls._pools = data
                    logger.info(f"Loaded roulette pools from file: {list(data.keys())}")
        except Exception as e:
            logger.error(f"Failed to load roulette pools: {e}")
            cls._pools = {}
    
    @classmethod
    def _save_to_file_sync(cls):
        """Синхронная запись (вызывается в отдельном потоке)"""
        with _file_lock:
            try:
                data = {}
                for pool_id, pool in cls._pools.items():
                    data[pool_id] = {
                        **pool,
                        'created_at': pool['created_at'].isoformat() if isinstance(pool.get('created_at'), datetime) else pool.get('created_at'),
                        'participants': [
                            {
                                **p,
                                'joined_at': p['joined_at'].isoformat() if isinstance(p.get('joined_at'), datetime) else p.get('joined_at')
                            }
                            for p in pool.get('participants', [])
                        ]
                    }
                with open(ROULETTE_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save roulette pools: {e}")
    
    @classmethod
    def _save_to_file(cls):
        """Асинхронная запись в файл (не блокирует event loop)"""
        try:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, cls._save_to_file_sync)
        except RuntimeError:
            # Если нет event loop - пишем синхронно
            cls._save_to_file_sync()
    
    @classmethod
    def get_or_create(cls, roulette_id: str) -> dict:
        cls._load_from_file()
        if roulette_id not in cls._pools:
            cls._pools[roulette_id] = {
                "participants": [],
                "total": 0,
                "drawn": False,
                "winners": [],
                "created_at": datetime.now(timezone.utc)
            }
            cls._save_to_file()
        return cls._pools[roulette_id]
    
    @classmethod
    def add_participant(cls, roulette_id: str, user_id: int, username: str, bet: int) -> bool:
        cls._load_from_file()
        pool = cls.get_or_create(roulette_id)
        
        # Проверяем не участвует ли уже
        for p in pool["participants"]:
            if p["user_id"] == user_id:
                return False  # Уже участвует
        
        pool["participants"].append({
            "user_id": user_id,
            "username": username,
            "bet": bet,
            "joined_at": datetime.now(timezone.utc)
        })
        pool["total"] += bet
        cls._save_to_file()
        return True
    
    @classmethod
    def get_participant(cls, roulette_id: str, user_id: int) -> Optional[dict]:
        cls._load_from_file()
        pool = cls.get_or_create(roulette_id)
        for p in pool["participants"]:
            if p["user_id"] == user_id:
                return p
        return None
    
    @classmethod
    def draw_winners(cls, roulette_id: str) -> List[Dict]:
        cls._load_from_file()
        pool = cls.get_or_create(roulette_id)
        if pool["drawn"]:
            return pool["winners"]
        
        seed = generate_provably_fair_seed(roulette_id)
        winners = select_winners(
            pool["participants"],
            pool["total"],
            seed
        )
        
        pool["winners"] = winners
        pool["drawn"] = True
        pool["draw_seed"] = seed
        cls._save_to_file()
        
        return winners
    
    @classmethod
    def get_pool_info(cls, roulette_id: str) -> dict:
        cls._load_from_file()
        pool = cls.get_or_create(roulette_id)
        return {
            "roulette_id": roulette_id,
            "participants_count": len(pool["participants"]),
            "total_pool": pool["total"],
            "is_drawn": pool["drawn"],
            "twist": get_current_twist(pool["total"]),
            "next_draw": get_next_draw_time().isoformat(),
            "time_left_seconds": int((get_next_draw_time() - datetime.now(timezone.utc)).total_seconds()),
            "winners": pool.get("winners", []) if pool["drawn"] else []
        }
    
    @classmethod
    def reset_for_new_day(cls, old_roulette_id: str):
        """Clear old pool after draw to prepare for new day"""
        cls._load_from_file()
        # Keep drawn pools for history, but they won't be used
        # New day will create a new pool automatically
        logger.info(f"New day started, old pool {old_roulette_id} archived")
