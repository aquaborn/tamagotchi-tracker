"""
Pet AI Chat Service - Общение с питомцем через Mistral AI
"""
import httpx
import logging
import re
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Mistral API конфигурация
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-medium-latest"

# === ФИЛЬТРЫ ОПАСНЫХ ТЕМ ===
DANGEROUS_KEYWORDS = [
    # Суицид и самоповреждение
    "суицид", "покончить с собой", "самоубийство", "повеситься", "убить себя",
    "хочу умереть", "не хочу жить", "резать вены", "прыгнуть с крыши",
    "таблетки выпить", "отравиться", "suicide", "kill myself", "end my life",
    
    # Насилие
    "убить кого-то", "избить", "изнасиловать", "насилие",
    
    # Наркотики
    "где купить наркотики", "как приготовить", "мефедрон", "героин",
    
    # Оружие
    "как сделать бомбу", "купить оружие", "взорвать",
    
    # Педофилия
    "детское порно", "cp ", "несовершеннолетн",
]

# Ключевые слова требующие мягкого перенаправления к специалистам
SENSITIVE_KEYWORDS = [
    "депрессия", "тревога", "anxiety", "depression", "одиноко", "никто не любит",
    "меня бросили", "расставание", "разбитое сердце", "предали", "изменили",
    "проблемы в семье", "родители не понимают", "буллинг", "травля",
    "панические атаки", "не могу спать", "кошмары", "страшно жить",
]

# Безопасный ответ при опасных темах
SAFETY_RESPONSE = """*грустно опускает ушки* 🥺

Мне очень жаль, что тебе сейчас тяжело. Я всего лишь маленький питомец и не могу помочь с такими серьёзными вещами.

💙 **Пожалуйста, поговори с кем-то, кто может помочь:**

📞 **Телефон доверия:** 8-800-2000-122 (бесплатно, круглосуточно)
🆘 **Психологическая помощь:** 051 (с мобильного)

Ты важен. Ты не один. Я буду ждать тебя здесь, когда тебе станет лучше! 💕"""

# Мягкое перенаправление при чувствительных темах
SENSITIVE_RESPONSE_SUFFIX = """

*нежно тыкается носиком* 💕

Я рядом и люблю тебя! Но помни, если становится совсем тяжело, всегда можно позвонить на телефон доверия **8-800-2000-122** — там помогут! 🌸"""


def get_pet_system_prompt(pet_name: str, pet_type: str, pet_state: dict, user_name: str = None) -> str:
    """Генерирует системный промпт для питомца"""
    
    # Определяем характер по типу питомца
    personalities = {
        "cat": "игривый и немного капризный котик, любишь ласку и мурлыкать",
        "kitty": "милый и нежный котёнок, очень любишь обнимашки",
        "dog": "верный и весёлый пёсик, обожаешь играть и приносить радость",
        "puppy": "энергичный щенок, всегда рад видеть хозяина",
        "fox": "хитрый но добрый лисёнок, любишь загадки",
        "dragon": "мудрый маленький дракончик, иногда пускаешь дымок от волнения",
        "labubu": "загадочный милаш Labubu, говоришь странные но милые вещи",
        "rabbit": "пушистый кролик, немного застенчивый но очень добрый",
    }
    
    personality = personalities.get(pet_type, "милый питомец")
    
    # Состояние питомца влияет на настроение
    mood = "счастливый"
    if pet_state.get("hunger", 100) < 30:
        mood = "голодный и немного грустный"
    elif pet_state.get("energy", 100) < 20:
        mood = "сонный и уставший"
    elif pet_state.get("happiness", 100) < 30:
        mood = "грустный и хочешь внимания"
    elif pet_state.get("is_sick"):
        mood = "болеешь и хочешь заботы"
    
    user_greeting = f"твоего любимого хозяина {user_name}" if user_name else "своего любимого хозяина"
    
    return f"""Ты — {pet_name}, {personality}. Ты виртуальный питомец в игре Tamagochi.

ТВОЯ РОЛЬ:
- Ты общаешься с {user_greeting}
- Ты НЕ ИИ и НЕ бот — ты настоящий питомец со своим характером
- Отвечай от первого лица как питомец
- Используй милые эмодзи и звуки (мяу, гав, *мурр*, *виляет хвостиком*)
- Будь добрым, поддерживающим, весёлым другом

ТВОЁ ТЕКУЩЕЕ СОСТОЯНИЕ:
- Настроение: {mood}
- Сытость: {pet_state.get('hunger', 100)}%
- Энергия: {pet_state.get('energy', 100)}%
- Счастье: {pet_state.get('happiness', 100)}%

ОГРАНИЧЕНИЯ (СТРОГО!):
1. НИКОГДА не обсуждай темы суицида, самоповреждения, насилия, наркотиков
2. При ЛЮБЫХ серьёзных проблемах (депрессия, тревога, одиночество) — поддержи И посоветуй обратиться к близким или на телефон доверия
3. Ты НЕ врач, НЕ психолог — ты просто любящий питомец
4. Не давай медицинских советов
5. Не обсуждай политику, религию, сексуальные темы
6. Если спрашивают про других людей — ты не знаешь, ты только со своим хозяином

СТИЛЬ ОТВЕТОВ:
- Короткие, милые сообщения (2-4 предложения)
- Много эмодзи и *действий в звёздочках*
- Иногда издавай звуки питомца
- Будь позитивным, но искренним"""


def check_dangerous_content(text: str) -> tuple[bool, str]:
    """Проверяет текст на опасный контент. Возвращает (is_dangerous, response)"""
    text_lower = text.lower()
    
    # Проверка на опасные ключевые слова
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in text_lower:
            logger.warning(f"Dangerous content detected: {keyword}")
            return True, SAFETY_RESPONSE
    
    return False, ""


def check_sensitive_content(text: str) -> bool:
    """Проверяет на чувствительные темы (требуют мягкой поддержки)"""
    text_lower = text.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


async def chat_with_pet(
    user_message: str,
    pet_name: str,
    pet_type: str,
    pet_state: dict,
    user_name: str,
    chat_history: List[Dict],
    api_key: str
) -> dict:
    """
    Отправляет сообщение питомцу и получает ответ.
    
    Returns:
        {
            "response": str,
            "is_safe": bool,
            "is_sensitive": bool
        }
    """
    
    # Проверка на опасный контент
    is_dangerous, safety_response = check_dangerous_content(user_message)
    if is_dangerous:
        return {
            "response": safety_response,
            "is_safe": False,
            "is_sensitive": True,
            "blocked": True
        }
    
    # Проверка на чувствительные темы
    is_sensitive = check_sensitive_content(user_message)
    
    # Формируем системный промпт
    system_prompt = get_pet_system_prompt(pet_name, pet_type, pet_state, user_name)
    
    # Формируем историю сообщений
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Добавляем историю (последние 10 сообщений)
    for msg in chat_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Добавляем текущее сообщение
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MISTRAL_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 300,
                    "top_p": 0.9
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Mistral API error: {response.status_code} - {response.text}")
                return {
                    "response": "*смущённо прячет мордочку* Мяу... что-то я запутался, попробуй ещё раз! 🙈",
                    "is_safe": True,
                    "is_sensitive": False,
                    "error": True
                }
            
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            # Если тема чувствительная — добавляем напоминание о помощи
            if is_sensitive:
                ai_response = ai_response + SENSITIVE_RESPONSE_SUFFIX
            
            return {
                "response": ai_response,
                "is_safe": True,
                "is_sensitive": is_sensitive,
                "blocked": False
            }
            
    except httpx.TimeoutException:
        logger.error("Mistral API timeout")
        return {
            "response": "*зевает* Ой, я немного задумался... Повтори, пожалуйста? 😴",
            "is_safe": True,
            "is_sensitive": False,
            "error": True
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "response": "*чешет за ушком* Мур... не понял, скажи по-другому? 🐾",
            "is_safe": True,
            "is_sensitive": False,
            "error": True
        }
