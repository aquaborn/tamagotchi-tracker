from dataclasses import dataclass, field
from datetime import datetime, timezone
import random

@dataclass
class PetState:
    hunger: int       # 0..100 (100 = сытый)
    energy: int       # 0..100
    happiness: int    # 0..100
    hygiene: int = 100      # 0..100 (чистота) - NEW!
    health: int = 100       # 0..100 (здоровье) - NEW!
    discipline: int = 50    # 0..100 (дисциплина) - NEW!
    is_sick: bool = False   # болеет ли питомец
    is_sleeping: bool = False  # спит ли питомец
    light_off: bool = False    # выключен ли свет
    needs_attention: bool = False  # нужно ли внимание
    last_tick_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

def clamp(v: int) -> int:
    return max(0, min(100, v))

def apply_tick(state: PetState, now: datetime, weather_multipliers: dict = None) -> PetState:
    """Apply time-based stat changes with optional weather modifiers"""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    dt = (now - state.last_tick_at).total_seconds()
    if dt <= 0:
        return state
    
    weather_multipliers = weather_multipliers or {}
    
    # Базовая деградация каждые N секунд
    base_hunger_loss = int(dt // 600)   # -1 каждые 10 мин
    base_energy_loss = int(dt // 900)   # -1 каждые 15 мин
    base_hygiene_loss = int(dt // 800)  # -1 каждые ~13 мин (быстрее чем голод)
    
    # Применяем модификаторы погоды
    hunger_drain = weather_multipliers.get("hunger_drain", 1.0)
    energy_drain = weather_multipliers.get("energy_drain", 1.0)
    happiness_drain = weather_multipliers.get("happiness_drain", 1.0)
    
    hunger_loss = int(base_hunger_loss * hunger_drain)
    energy_loss = int(base_energy_loss * energy_drain)
    hygiene_loss = base_hygiene_loss
    
    # Если спит - энергия восстанавливается (УСКОРЕННО!)
    if state.is_sleeping and state.light_off:
        energy_loss = -int(dt // 60)   # +1 каждую минуту (быстро)
    elif state.is_sleeping:
        energy_loss = -int(dt // 120)  # +1 каждые 2 мин (медленнее со светом)
    
    new_hunger = clamp(state.hunger - hunger_loss)
    new_energy = clamp(state.energy - energy_loss)
    new_hygiene = clamp(state.hygiene - hygiene_loss)
    
    # happiness падает только при ОЧЕНЬ низких статах
    happiness_penalty = 0
    if new_hunger < 15:
        happiness_penalty += 1
    if new_hygiene < 20:
        happiness_penalty += 1
    # Применяем модификатор погоды к happiness
    happiness_penalty = int(happiness_penalty * happiness_drain)
    new_happiness = clamp(state.happiness - happiness_penalty)
    
    new_health = state.health
    new_is_sick = state.is_sick
    
    # === ЗДОРОВЬЕ: падает от критических показателей ===
    health_loss = 0
    
    # Низкий голод (< 20) - здоровье падает
    if new_hunger < 20:
        health_loss += int(dt // 600)  # -1 каждые 10 мин
    
    # Низкая энергия (< 15) - здоровье падает
    if new_energy < 15:
        health_loss += int(dt // 900)  # -1 каждые 15 мин
    
    # Низкая гигиена (< 20) - здоровье падает
    if new_hygiene < 20:
        health_loss += int(dt // 1200)  # -1 каждые 20 мин
    
    # Применяем потерю здоровья
    new_health = clamp(state.health - health_loss)
    
    # Шанс заболеть если критические показатели (5% шанс за тик)
    if not state.is_sick:
        critical_count = sum([
            new_hunger < 15,
            new_energy < 10,
            new_hygiene < 15,
            new_health < 50
        ])
        if critical_count >= 2:  # Если 2+ критических показателя
            if random.random() < 0.05:
                new_is_sick = True
                new_health = clamp(new_health - 15)
    
    # Если болеет - здоровье падает быстрее
    if new_is_sick:
        sickness_health_loss = int(dt // 300)  # -1 каждые 5 мин
        new_health = clamp(new_health - sickness_health_loss)
        new_happiness = clamp(new_happiness - 3)
    
    # Нужно внимание если критичные показатели
    needs_attention = (
        new_hunger < 20 or 
        new_energy < 20 or 
        new_hygiene < 30 or 
        new_is_sick or
        new_happiness < 30
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