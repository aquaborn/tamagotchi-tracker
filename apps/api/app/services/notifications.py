"""
Push Notifications Service - уведомления о состоянии питомца
"""
import asyncio
import httpx
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

# Telegram Bot Token (из settings)
BOT_TOKEN = None

def set_bot_token(token: str):
    global BOT_TOKEN
    BOT_TOKEN = token
    logger.info("Notification service initialized with bot token")

async def send_telegram_message(chat_id: int, text: str) -> tuple[bool, bool]:
    """
    Отправить сообщение через Telegram Bot API
    Returns: (success: bool, user_blocked: bool) - user_blocked=True если юзер заблокировал бота
    """
    if not BOT_TOKEN:
        logger.warning("Bot token not set, cannot send notification")
        return False, False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info(f"Notification sent to {chat_id}")
                return True, False
            else:
                error_data = response.json() if response.text else {}
                error_code = error_data.get("error_code")
                
                # 403 Forbidden - пользователь заблокировал бота
                if error_code == 403:
                    logger.warning(f"User {chat_id} blocked the bot, disabling notifications")
                    return False, True
                
                logger.error(f"Failed to send notification: {response.text}")
                return False, False
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False, False

# === КРИТИЧЕСКИЕ УВЕДОМЛЕНИЯ ===
NOTIFICATION_TYPES = {
    "hunger_critical": {
        "condition": lambda state: state.get("hunger", 100) < 20,
        "message": "🍖 <b>Твой питомец голодает!</b>\n\nСрочно покорми его, пока не поздно! Hunger: {hunger}%",
        "cooldown_hours": 4,
    },
    "energy_critical": {
        "condition": lambda state: state.get("energy", 100) < 15,
        "message": "😴 <b>Питомец очень устал!</b>\n\nУложи его спать! Energy: {energy}%",
        "cooldown_hours": 4,
    },
    "health_critical": {
        "condition": lambda state: state.get("health", 100) < 30,
        "message": "🏥 <b>Питомец болеет!</b>\n\nСрочно нужно лечение! Health: {health}%",
        "cooldown_hours": 2,
    },
    "pet_sick": {
        "condition": lambda state: state.get("is_sick", False),
        "message": "🤒 <b>Питомец заболел!</b>\n\nДай ему лекарство в приложении!",
        "cooldown_hours": 6,
    },
    "happiness_low": {
        "condition": lambda state: state.get("happiness", 100) < 25,
        "message": "😢 <b>Питомец грустит!</b>\n\nПоиграй с ним! Happiness: {happiness}%",
        "cooldown_hours": 6,
    },
    "hygiene_critical": {
        "condition": lambda state: state.get("hygiene", 100) < 20,
        "message": "🛁 <b>Питомец грязный!</b>\n\nПора искупать! Hygiene: {hygiene}%",
        "cooldown_hours": 8,
    },
}

# === ЗАВЛЕКАЮЩИЕ УВЕДОМЛЕНИЯ ===
ENGAGEMENT_MESSAGES = [
    # Питомец скучает
    "🐾 <b>Твой питомец скучает!</b>\n\nОн ждёт тебя уже давно... 🥺",
    "👀 <b>Алло!</b>\n\nТвой пушистый друг смотрит в окно и грустит...",
    "🌟 <b>Не забывай обо мне!</b>\n\nТвой питомец скучает по тебе 💕",
    "🎮 <b>Время играть!</b>\n\nТвой питомец хочет поиграть с тобой!",
    
    # Рулетка
    "🎰 <b>Рулетка ждёт!</b>\n\nСделай ставку и выиграй звёзды! ⭐",
    "🌟 <b>Банк рулетки растёт!</b>\n\nУспей сделать ставку до розыгрыша!",
    "💰 <b>Скоро розыгрыш!</b>\n\nНе пропусти шанс выиграть! 🎉",
    
    # Мотивация
    "💪 <b>Время прокачиваться!</b>\n\nЗайди и подними свой уровень!",
    "🏆 <b>Рейтинг обновился!</b>\n\nПроверь свою позицию в лидерборде!",
    "🛒 <b>Новые товары в магазине!</b>\n\nПриодень своего питомца! 👑",
    
    # Серии
    "🔥 <b>Не потеряй серию!</b>\n\nЗайди сегодня чтобы сохранить streak!",
    "💫 <b>Твоя серия под угрозой!</b>\n\nЗайди сейчас и покорми питомца!",
    
    # Погода
    "☀️ <b>Отличная погода!</b>\n\nТвой питомец хочет гулять! 😊",
    "⛈️ <b>Гроза надвигается!</b>\n\nПроверь своего питомца - он боится!",
    "❄️ <b>Холодно!</b>\n\nУкрой питомца в домике 🏠",
    
    # Прикольные
    "😺 <b>Мяу!</b>\n\nТвой питомец передаёт привет! 👋",
    "😴 <b>*зевает*</b>\n\nТвой питомец только проснулся и ждёт завтрак!",
    "🍕 <b>Пиццу заказывали?</b>\n\nШутка! Но питомец голоден... 😋",
    "🌜 <b>Доброй ночи!</b>\n\nНе забудь уложить питомца спать 🐤",
    "🌞 <b>Доброе утро!</b>\n\nТвой питомец уже проснулся и ждёт тебя!",
    "🏝️ <b>Мечтает об отпуске...</b>\n\nТвой питомец хочет на море! 🌊",
    "📸 <b>Фотосессия!</b>\n\nТвой питомец готов к фото! 😎",
    "🎂 <b>Сюрприз!</b>\n\nЗайди и посмотри что нового!",
]

# Сообщения по времени суток
TIME_BASED_MESSAGES = {
    "morning": [  # 6-11
        "🌞 <b>Доброе утро!</b>\n\nТвой питомец проснулся и хочет завтрак!",
        "☕ <b>Утренний кофе?</b>\n\nА питомцу нужен завтрак! 🍖",
        "🌟 <b>Начни день с заботы!</b>\n\nПокорми своего питомца!",
    ],
    "afternoon": [  # 12-17
        "🍝 <b>Обеденный перерыв!</b>\n\nПоиграй с питомцем 🎮",
        "😊 <b>Как дела?</b>\n\nТвой питомец передаёт привет!",
        "🌞 <b>Солнечный день!</b>\n\nИдеально для игры с питомцем!",
    ],
    "evening": [  # 18-22
        "🌙 <b>Добрый вечер!</b>\n\nНе забудь покормить питомца ужином!",
        "🎰 <b>Вечерняя рулетка!</b>\n\nСкоро розыгрыш! Успей сделать ставку!",
        "🐾 <b>Вечерние игры!</b>\n\nПитомец хочет поиграть перед сном!",
    ],
    "night": [  # 23-5
        "🌜 <b>Спокойной ночи!</b>\n\nУложи питомца спать 💤",
        "🐤 <b>Пора баиньки!</b>\n\nВыключи свет для питомца!",
    ]
}

# Хранение cooldowns в памяти (user_id -> {notification_type -> last_sent})
_notification_cooldowns: Dict[int, Dict[str, datetime]] = {}
_engagement_cooldowns: Dict[int, datetime] = {}  # Для завлекающих уведомлений

def can_send_notification(user_id: int, notification_type: str) -> bool:
    """Проверить можно ли отправить уведомление (cooldown)"""
    if user_id not in _notification_cooldowns:
        return True
    
    user_cooldowns = _notification_cooldowns[user_id]
    if notification_type not in user_cooldowns:
        return True
    
    last_sent = user_cooldowns[notification_type]
    cooldown_hours = NOTIFICATION_TYPES[notification_type]["cooldown_hours"]
    
    return datetime.now(timezone.utc) > last_sent + timedelta(hours=cooldown_hours)

def mark_notification_sent(user_id: int, notification_type: str):
    """Отметить что уведомление отправлено"""
    if user_id not in _notification_cooldowns:
        _notification_cooldowns[user_id] = {}
    _notification_cooldowns[user_id][notification_type] = datetime.now(timezone.utc)

async def check_and_notify_user(
    telegram_id: int,
    pet_state: dict,
    notifications_enabled: bool = True,
    db: AsyncSession = None
) -> tuple[List[str], bool]:
    """
    Проверить состояние питомца и отправить уведомления если нужно
    Returns: (sent_notifications, user_blocked)
    """
    if not notifications_enabled:
        return [], False
    
    sent_notifications = []
    user_blocked = False
    
    for ntype, config in NOTIFICATION_TYPES.items():
        # Проверяем условие
        if not config["condition"](pet_state):
            continue
        
        # Проверяем cooldown
        if not can_send_notification(telegram_id, ntype):
            continue
        
        # Форматируем сообщение
        message = config["message"].format(**pet_state)
        message += "\n\n🎮 <i>Открой приложение и позаботься о питомце!</i>"
        
        # Отправляем
        success, blocked = await send_telegram_message(telegram_id, message)
        if blocked:
            user_blocked = True
            break  # Пользователь заблокировал бота, прерываем
        if success:
            mark_notification_sent(telegram_id, ntype)
            sent_notifications.append(ntype)
            logger.info(f"Sent {ntype} notification to {telegram_id}")
    
    return sent_notifications, user_blocked

async def send_roulette_result_notification(
    telegram_id: int,
    winner_data: dict,
    pool_total: int
) -> bool:
    """Уведомить победителя рулетки"""
    place_emoji = ["🥇", "🥈", "🥉"][winner_data["place"]-1] if winner_data["place"] <= 3 else "🎖️"
    vpn_text = f"\n🛡️ Бонус: {winner_data['vpn_bonus']}ч VPN!" if winner_data.get("vpn_bonus", 0) > 0 else ""
    
    message = f"""
🎰 <b>STAR ROULETTE - ТЫ ПОБЕДИЛ!</b> 🎉

{place_emoji} <b>Место: #{winner_data['place']}</b>
💰 <b>Выигрыш: {winner_data['prize']} ⭐</b>{vpn_text}

👥 Всего в банке было: {pool_total} ⭐

<i>Звёзды уже на твоём балансе!</i>
"""
    return await send_telegram_message(telegram_id, message)

async def send_daily_reminder(telegram_id: int, pet_name: str = "Питомец") -> bool:
    """Ежедневное напоминание зайти в игру"""
    message = f"""
🌟 <b>Привет!</b>

Твой {pet_name} ждёт тебя! 🐾
Не забудь покормить и поиграть с ним сегодня.

⭐ Участвуй в ежедневной рулетке!
📈 Поднимайся в рейтинге!

<i>Нажми чтобы открыть игру</i>
"""
    return await send_telegram_message(telegram_id, message)


# === ЗАВЛЕКАЮЩИЕ УВЕДОМЛЕНИЯ ===
def get_time_period() -> str:
    """Получить текущий период суток"""
    hour = datetime.now(timezone.utc).hour + 3  # MSK
    if hour >= 24:
        hour -= 24
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 23:
        return "evening"
    else:
        return "night"

def can_send_engagement(user_id: int, cooldown_hours: int = 6) -> bool:
    """Проверить можно ли отправить завлекающее уведомление"""
    if user_id not in _engagement_cooldowns:
        return True
    
    last_sent = _engagement_cooldowns[user_id]
    return datetime.now(timezone.utc) > last_sent + timedelta(hours=cooldown_hours)

def mark_engagement_sent(user_id: int):
    """Отметить отправку завлекающего уведомления"""
    _engagement_cooldowns[user_id] = datetime.now(timezone.utc)

async def send_engagement_notification(telegram_id: int, last_activity: datetime = None) -> tuple[bool, bool]:
    """
    Отправить завлекающее уведомление
    Выбирает сообщение в зависимости от времени суток и рандома
    Returns: (success, user_blocked)
    """
    # Проверяем cooldown (не чаще раза в 6 часов)
    if not can_send_engagement(telegram_id, cooldown_hours=6):
        return False, False
    
    # Выбираем тип сообщения
    period = get_time_period()
    
    # 40% шанс - сообщение по времени суток, 60% - общее
    if random.random() < 0.4 and period in TIME_BASED_MESSAGES:
        message = random.choice(TIME_BASED_MESSAGES[period])
    else:
        message = random.choice(ENGAGEMENT_MESSAGES)
    
    # Добавляем CTA
    message += "\n\n🎮 <i>Нажми чтобы открыть игру!</i>"
    
    success, blocked = await send_telegram_message(telegram_id, message)
    if blocked:
        return False, True
    
    if success:
        mark_engagement_sent(telegram_id)
        logger.info(f"Sent engagement notification to {telegram_id}")
        return True, False
    
    return False, False

async def send_inactivity_reminder(telegram_id: int, hours_inactive: int) -> tuple[bool, bool]:
    """
    Напоминание для неактивных пользователей
    Returns: (success, user_blocked)
    """
    if hours_inactive < 12:
        return False, False
    
    if not can_send_engagement(telegram_id, cooldown_hours=12):
        return False, False
    
    if hours_inactive < 24:
        message = "🐾 <b>Твой питомец скучает!</b>\n\nТы не заходил уже давно... Он ждёт тебя! 🥺"
    elif hours_inactive < 48:
        message = "😿 <b>Питомец загрустил...</b>\n\nТы пропал на целый день! Он очень скучает..."
    elif hours_inactive < 72:
        message = "🆘 <b>SOS!</b>\n\nТвой питомец давно не ел и не играл! Срочно зайди!"
    else:
        message = "💔 <b>Не бросай меня...</b>\n\nТвой питомец очень ждёт тебя! Он голодает и грустит 😢"
    
    message += "\n\n🎮 <i>Открой игру и позаботься о питомце!</i>"
    
    success, blocked = await send_telegram_message(telegram_id, message)
    if blocked:
        return False, True
    
    if success:
        mark_engagement_sent(telegram_id)
        logger.info(f"Sent inactivity reminder to {telegram_id} (inactive {hours_inactive}h)")
        return True, False
    
    return False, False


# === BACKGROUND TASK для рассылки уведомлений ===
_background_task_running = False

async def engagement_notification_worker(db_session_factory):
    """
    Фоновая задача для периодической рассылки завлекающих уведомлений.
    Запускается при старте приложения.
    """
    global _background_task_running
    _background_task_running = True
    
    logger.info("Engagement notification worker started")
    
    while _background_task_running:
        try:
            # Ждем 30 минут между итерациями
            await asyncio.sleep(30 * 60)  # 30 минут
            
            # Не отправляем ночью (23:00 - 07:00 MSK)
            hour = (datetime.now(timezone.utc).hour + 3) % 24
            if hour >= 23 or hour < 7:
                logger.debug("Skipping engagement notifications during night hours")
                continue
            
            # Получаем пользователей с питомцами
            async with db_session_factory() as db:
                from app.models.user import User
                from app.models.pet import PetModel as Pet
                
                # Пользователи с низкими показателями питомца или неактивные
                result = await db.execute(
                    select(User, Pet)
                    .join(Pet, User.telegram_id == Pet.user_id)
                    .where(User.notifications_enabled == True)
                )
                users_pets = result.all()
                
                sent_count = 0
                blocked_users = []  # Список пользователей, заблокировавших бота
                
                for user, pet in users_pets:
                    # Не спамим - максимум 50 уведомлений за итерацию
                    if sent_count >= 50:
                        break
                    
                    user_blocked = False
                    
                    # Проверяем неактивность
                    if pet.last_tick_at:
                        hours_inactive = (datetime.now(timezone.utc) - pet.last_tick_at).total_seconds() / 3600
                        
                        # Если неактивен более 12 часов - отправляем напоминание
                        if hours_inactive >= 12:
                            success, blocked = await send_inactivity_reminder(user.telegram_id, int(hours_inactive))
                            if blocked:
                                user_blocked = True
                            elif success:
                                sent_count += 1
                            
                            if user_blocked:
                                blocked_users.append(user)
                            continue
                    
                    if not user_blocked:
                        # Проверяем низкие показатели
                        pet_state = {
                            "hunger": pet.hunger,
                            "energy": pet.energy,
                            "happiness": pet.happiness,
                            "hygiene": pet.hygiene,
                            "health": pet.health,
                            "is_sick": pet.is_sick
                        }
                        
                        # Если есть критические состояния - проверяем и отправляем
                        any_critical = (
                            pet.hunger < 30 or 
                            pet.energy < 20 or 
                            pet.happiness < 30 or 
                            pet.hygiene < 25 or
                            pet.health < 40 or
                            pet.is_sick
                        )
                        
                        if any_critical:
                            sent, blocked = await check_and_notify_user(user.telegram_id, pet_state, True)
                            if blocked:
                                user_blocked = True
                                blocked_users.append(user)
                            elif sent:
                                sent_count += len(sent)
                                continue
                    
                    # Иначе - шанс отправить завлекающее уведомление (10%)
                    if not user_blocked and random.random() < 0.1:
                        success, blocked = await send_engagement_notification(user.telegram_id)
                        if blocked:
                            blocked_users.append(user)
                        elif success:
                            sent_count += 1
                
                # Отключаем уведомления для пользователей, заблокировавших бота
                if blocked_users:
                    for user in blocked_users:
                        user.notifications_enabled = False
                        logger.info(f"Disabled notifications for user {user.telegram_id} (blocked bot)")
                    await db.commit()
                    logger.info(f"Disabled notifications for {len(blocked_users)} users who blocked the bot")
                
                logger.info(f"Engagement worker: sent {sent_count} notifications")
                
        except Exception as e:
            logger.error(f"Error in engagement worker: {e}")
            await asyncio.sleep(60)  # При ошибке ждем минуту
    
    logger.info("Engagement notification worker stopped")

async def stop_engagement_worker():
    """Остановить фоновую задачу"""
    global _background_task_running
    _background_task_running = False
