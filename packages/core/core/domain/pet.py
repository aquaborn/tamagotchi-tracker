from dataclasses import dataclass, field
from datetime import datetime, timezone
import random

# =============================================================================
# НОВАЯ СИСТЕМА СТАТОВ - "Цикл жизни питомца"
# Пользователь заходит 3 раза в день: Утро (покормить), День (поиграть), Вечер (помыть/уложить)
# =============================================================================

# Конфигурация скоростей деградации (в секундах)
DECAY_CONFIG = {
    # Голод - "Таймер выживания"
    "hunger_interval": 1200,        # -1 каждые 20 мин базово
    "hunger_awake_multiplier": 1.5, # x1.5 если не спит
    "hunger_critical": 20,          # Ниже этого - штрафы
    "hunger_starving": 5,           # Ниже этого - теряем здоровье
    
    # Энергия - "Ресурс для действий"
    "energy_interval": 2400,        # -1 каждые 40 мин пассивно
    "energy_sleep_recovery": 5,     # +1 каждые 5 сек во сне с выключенным светом (+12/мин)
    "energy_sleep_light_on": 10,    # +1 каждые 10 сек если свет включен (+6/мин)
    "energy_awake_recovery": 300,   # +1 каждые 5 мин бодрствуя (очень медленно)
    "energy_min_for_play": 10,      # Минимум для игр
    
    # Гигиена - "Событийный стат" (медленно падает сама, быстро от действий)
    "hygiene_interval": 1800,       # -1 каждые 30 мин пассивно (было 2 часа - слишком медленно)
    "hygiene_critical": 30,         # Ниже этого - риск болезни x2, счастье x2
    "hygiene_dirty": 20,            # Ниже этого - "Грязнуля"
    
    # Счастье - "Множитель прогресса"
    "happiness_base_decay": 3600,       # -1 каждый час базово (питомцу нужно внимание)
    "happiness_hunger_threshold": 50,   # Еда ниже 50% -> счастье падает
    "happiness_hygiene_threshold": 40,  # Гигиена ниже 40% -> счастье падает  
    "happiness_energy_threshold": 30,   # Энергия ниже 30% -> счастье падает
    "happiness_decay_interval": 600,    # -1 каждые 10 мин при плохих статах
    "happiness_bonus_threshold": 80,    # Выше 80% - бонус к оффлайн доходу
    "happiness_runaway_threshold": 30,  # Ниже 30% - риск побега/болезни
    
    # Здоровье - "Защитный слой" (падает только при критических условиях)
    "health_starvation_interval": 1800, # -5 каждые 30 мин если голод < 5
    "health_starvation_damage": 5,
    "health_sickness_interval": 600,    # -2 каждые 10 мин если болен
    "health_sickness_damage": 2,
    
    # Болезнь
    "sickness_base_chance": 0.03,       # 3% базовый шанс заболеть за тик
    "sickness_dirty_multiplier": 2.0,   # x2 если грязный
}

# Стоимость действий (для apply_action)
ACTION_COSTS = {
    "play_ball": {"energy": -15, "hygiene": -15, "happiness": +20},
    "play_toy": {"energy": -10, "hygiene": -10, "happiness": +15},
    "train": {"energy": -20, "hygiene": -5, "happiness": +5, "discipline": +10},
    "walk": {"energy": -10, "hygiene": -20, "happiness": +25},
    "feed": {"hunger": +30, "hygiene": -10, "happiness": +5},
    "feed_treat": {"hunger": +15, "hygiene": -5, "happiness": +15},
    "clean": {"hygiene": +40, "happiness": +5},
    "bath": {"hygiene": +100, "happiness": +10, "energy": -5},
    "pet": {"happiness": +10},
    "medicine": {"health": +30, "happiness": -10},  # Лекарство невкусное
    "sleep": {},  # Обрабатывается отдельно через is_sleeping
    "wake": {},
}

@dataclass
class PetState:
    hunger: int       # 0..100 (100 = сытый)
    energy: int       # 0..100
    happiness: int    # 0..100
    hygiene: int = 100      # 0..100 (чистота)
    health: int = 100       # 0..100 (здоровье)
    discipline: int = 50    # 0..100 (дисциплина)
    is_sick: bool = False   # болеет ли питомец
    is_sleeping: bool = False  # спит ли питомец
    light_off: bool = False    # выключен ли свет
    needs_attention: bool = False  # нужно ли внимание
    last_tick_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

def clamp(v: int) -> int:
    return max(0, min(100, v))

def apply_tick(state: PetState, now: datetime, weather_multipliers: dict = None) -> PetState:
    """
    Новая система деградации статов:
    - Голод падает быстрее если бодрствует
    - Энергия почти не падает пассивно, но быстро восстанавливается во сне
    - Гигиена падает очень медленно (основное падение от действий)
    - Счастье падает если другие статы низкие
    - Здоровье падает только при голодании или болезни
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    dt = (now - state.last_tick_at).total_seconds()
    if dt <= 0:
        return state
    
    cfg = DECAY_CONFIG
    weather = weather_multipliers or {}
    
    # ==================== ГОЛОД ====================
    # Базово: -1 каждые 20 мин
    # Если бодрствует: x1.5 быстрее
    hunger_interval = cfg["hunger_interval"]
    if not state.is_sleeping:
        hunger_interval = hunger_interval / cfg["hunger_awake_multiplier"]
    
    # Погодный модификатор (снег/шторм = больше еды)
    hunger_interval = hunger_interval / weather.get("hunger_drain", 1.0)
    
    hunger_loss = int(dt // hunger_interval) if hunger_interval > 0 else 0
    new_hunger = clamp(state.hunger - hunger_loss)
    
    # ==================== ЭНЕРГИЯ ====================
    if state.is_sleeping:
        # Сон: быстрое восстановление
        if state.light_off:
            # +1 каждые 5 сек = +12 в минуту (полное восстановление за ~8 мин)
            energy_gain = int(dt // cfg["energy_sleep_recovery"])
        else:
            # Свет мешает: +1 каждые 10 сек = +6 в минуту
            energy_gain = int(dt // cfg["energy_sleep_light_on"])
        new_energy = clamp(state.energy + energy_gain)
    else:
        # Бодрствование: медленная потеря, очень медленное восстановление если отдыхает
        energy_interval = cfg["energy_interval"] / weather.get("energy_drain", 1.0)
        energy_loss = int(dt // energy_interval) if energy_interval > 0 else 0
        new_energy = clamp(state.energy - energy_loss)
    
    # ==================== ГИГИЕНА ====================
    # Очень медленное пассивное падение (-1 каждые 2 часа)
    # Основное падение - от действий (кормление, игры)
    hygiene_loss = int(dt // cfg["hygiene_interval"])
    new_hygiene = clamp(state.hygiene - hygiene_loss)
    
    # ==================== СЧАСТЬЕ ====================
    # Базовое падение + ускоренное если другие статы плохие
    happiness_decay_rate = 0
    happiness_multiplier = weather.get("happiness_drain", 1.0)
    
    # Базовое падение -1 каждый час (питомцу нужно внимание!)
    base_happiness_loss = int(dt // cfg.get("happiness_base_decay", 3600))
    
    # Голодный питомец грустит
    if new_hunger < cfg["happiness_hunger_threshold"]:
        happiness_decay_rate += 1
        if new_hunger < 20:  # Очень голодный - ещё быстрее
            happiness_decay_rate += 1
    
    # Грязный питомец грустит (x2 скорость если критично)
    if new_hygiene < cfg["happiness_hygiene_threshold"]:
        happiness_decay_rate += 1
        if new_hygiene < cfg["hygiene_dirty"]:
            happiness_decay_rate += 1  # "Грязнуля" - двойной штраф
    
    # Уставший питомец грустит
    if new_energy < cfg["happiness_energy_threshold"]:
        happiness_decay_rate += 1
    
    # Применяем погодный модификатор
    happiness_decay_rate = int(happiness_decay_rate * happiness_multiplier)
    
    # Рассчитываем потерю счастья
    happiness_loss = base_happiness_loss  # Базовое падение (-1/час)
    if happiness_decay_rate > 0:
        # +дополнительно -1 каждые 10 мин за каждый фактор
        ticks = int(dt // cfg["happiness_decay_interval"])
        happiness_loss += ticks * happiness_decay_rate
    
    new_happiness = clamp(state.happiness - happiness_loss)
    
    # ==================== ЗДОРОВЬЕ ====================
    new_health = state.health
    new_is_sick = state.is_sick
    
    # Здоровье падает ТОЛЬКО при критических условиях:
    
    # 1. Голодание (hunger < 5) - прямой урон здоровью
    if new_hunger < cfg["hunger_starving"]:
        starvation_damage = int(dt // cfg["health_starvation_interval"]) * cfg["health_starvation_damage"]
        new_health = clamp(new_health - starvation_damage)
    
    # 2. Болезнь - постоянный урон
    if new_is_sick:
        sickness_damage = int(dt // cfg["health_sickness_interval"]) * cfg["health_sickness_damage"]
        new_health = clamp(new_health - sickness_damage)
        # Больной питомец ещё и грустный
        new_happiness = clamp(new_happiness - int(dt // 600))  # -1 каждые 10 мин
    
    # ==================== БОЛЕЗНЬ ====================
    # Шанс заболеть если грязный или с низким здоровьем
    if not new_is_sick:
        sickness_chance = cfg["sickness_base_chance"]
        
        # Грязный питомец болеет чаще
        if new_hygiene < cfg["hygiene_critical"]:
            sickness_chance *= cfg["sickness_dirty_multiplier"]
        
        # Низкое здоровье = выше шанс
        if new_health < 50:
            sickness_chance *= 1.5
        
        # Проверяем шанс за каждые 10 минут прошедшего времени
        checks = max(1, int(dt // 600))
        for _ in range(checks):
            if random.random() < sickness_chance:
                new_is_sick = True
                new_health = clamp(new_health - 10)  # Сразу -10 здоровья при заболевании
                break
    
    # ==================== NEEDS ATTENTION ====================
    needs_attention = (
        new_hunger < cfg["hunger_critical"] or 
        new_energy < cfg["energy_min_for_play"] or 
        new_hygiene < cfg["hygiene_critical"] or 
        new_happiness < cfg["happiness_runaway_threshold"] or
        new_is_sick
    )
    
    return PetState(
        hunger=new_hunger,
        energy=new_energy,
        happiness=new_happiness,
        hygiene=new_hygiene,
        health=new_health,
        discipline=state.discipline,
        is_sick=new_is_sick,
        is_sleeping=state.is_sleeping,
        light_off=state.light_off,
        needs_attention=needs_attention,
        last_tick_at=now,
    )


def apply_action(state: PetState, action: str, now: datetime = None) -> tuple[PetState, dict]:
    """
    Применить действие к питомцу.
    Возвращает (новый_стейт, результат).
    
    Результат содержит:
    - success: bool
    - message: str
    - stat_changes: dict изменений
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Сначала применяем тик времени
    state = apply_tick(state, now)
    
    result = {
        "success": False,
        "message": "",
        "stat_changes": {}
    }
    
    # Проверка: можно ли выполнить действие?
    
    # Спящий питомец не может играть
    if state.is_sleeping and action in ["play_ball", "play_toy", "train", "walk", "feed"]:
        result["message"] = "Питомец спит! Сначала разбудите его."
        return state, result
    
    # Недостаточно энергии для активных действий
    energy_actions = ["play_ball", "play_toy", "train", "walk"]
    if action in energy_actions:
        cost = abs(ACTION_COSTS.get(action, {}).get("energy", 0))
        if state.energy < cost:
            result["message"] = f"Недостаточно энергии! Нужно {cost}, есть {state.energy}. Уложите питомца спать."
            return state, result
    
    # Получаем стоимость действия
    costs = ACTION_COSTS.get(action, {})
    if not costs and action not in ["sleep", "wake"]:
        result["message"] = f"Неизвестное действие: {action}"
        return state, result
    
    # Применяем изменения статов
    new_hunger = clamp(state.hunger + costs.get("hunger", 0))
    new_energy = clamp(state.energy + costs.get("energy", 0))
    new_happiness = clamp(state.happiness + costs.get("happiness", 0))
    new_hygiene = clamp(state.hygiene + costs.get("hygiene", 0))
    new_health = clamp(state.health + costs.get("health", 0))
    new_discipline = clamp(state.discipline + costs.get("discipline", 0))
    new_is_sleeping = state.is_sleeping
    new_is_sick = state.is_sick
    
    # Специальные действия
    if action == "sleep":
        new_is_sleeping = True
        result["message"] = "Питомец уснул. Энергия будет восстанавливаться."
    elif action == "wake":
        new_is_sleeping = False
        result["message"] = "Питомец проснулся!"
    elif action == "medicine" and state.is_sick:
        new_is_sick = False
        result["message"] = "Питомец выздоровел!"
    elif action == "medicine" and not state.is_sick:
        result["message"] = "Питомец не болен, лекарство не нужно."
        return state, result
    elif action == "bath":
        result["message"] = "Питомец теперь чистый и довольный!"
    elif action == "feed":
        result["message"] = "Питомец покушал! Но немного испачкался."
    elif action in ["play_ball", "play_toy"]:
        result["message"] = "Питомец поиграл и стал счастливее! Но устал и испачкался."
    elif action == "walk":
        result["message"] = "Отличная прогулка! Питомец счастлив, но испачкался."
    elif action == "pet":
        result["message"] = "Питомцу приятно! 💕"
    else:
        result["message"] = f"Действие '{action}' выполнено."
    
    result["success"] = True
    result["stat_changes"] = costs
    
    # Пересчитываем needs_attention
    cfg = DECAY_CONFIG
    needs_attention = (
        new_hunger < cfg["hunger_critical"] or 
        new_energy < cfg["energy_min_for_play"] or 
        new_hygiene < cfg["hygiene_critical"] or 
        new_happiness < cfg["happiness_runaway_threshold"] or
        new_is_sick
    )
    
    new_state = PetState(
        hunger=new_hunger,
        energy=new_energy,
        happiness=new_happiness,
        hygiene=new_hygiene,
        health=new_health,
        discipline=new_discipline,
        is_sick=new_is_sick,
        is_sleeping=new_is_sleeping,
        light_off=state.light_off,
        needs_attention=needs_attention,
        last_tick_at=now,
    )
    
    return new_state, result


def get_offline_bonus_multiplier(happiness: int) -> float:
    """
    Бонус к оффлайн-доходу в зависимости от счастья.
    happiness > 80: +20% бонус
    happiness > 60: +10% бонус  
    happiness < 30: -50% штраф
    """
    if happiness >= 80:
        return 1.2
    elif happiness >= 60:
        return 1.1
    elif happiness < 30:
        return 0.5
    return 1.0


def can_perform_action(state: PetState, action: str) -> tuple[bool, str]:
    """
    Проверить, может ли питомец выполнить действие.
    Возвращает (можно, причина_если_нет).
    """
    if state.is_sleeping and action in ["play_ball", "play_toy", "train", "walk", "feed"]:
        return False, "Питомец спит"
    
    energy_actions = ["play_ball", "play_toy", "train", "walk"]
    if action in energy_actions:
        cost = abs(ACTION_COSTS.get(action, {}).get("energy", 0))
        if state.energy < cost:
            return False, f"Мало энергии ({state.energy}/{cost})"
    
    if action == "medicine" and not state.is_sick:
        return False, "Питомец здоров"
    
    return True, "OK"