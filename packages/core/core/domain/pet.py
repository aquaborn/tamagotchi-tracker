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

def apply_tick(state: PetState, now: datetime) -> PetState:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    dt = (now - state.last_tick_at).total_seconds()
    if dt <= 0:
        return state

    # Деградация каждые N минут
    hunger_loss = int(dt // 600)   # -1 каждые 10 мин
    energy_loss = int(dt // 900)   # -1 каждые 15 мин
    hygiene_loss = int(dt // 1200) # -1 каждые 20 мин (чистота)
    
    # Если спит с выключенным светом - энергия восстанавливается быстрее
    if state.is_sleeping and state.light_off:
        energy_loss = -int(dt // 300)  # +1 каждые 5 мин
    elif state.is_sleeping:
        energy_loss = -int(dt // 600)  # +1 каждые 10 мин (без света медленнее)
    
    new_hunger = clamp(state.hunger - hunger_loss)
    new_energy = clamp(state.energy - energy_loss)
    new_hygiene = clamp(state.hygiene - hygiene_loss)
    new_happiness = clamp(state.happiness - (1 if new_hunger < 20 or new_hygiene < 30 else 0))
    new_health = state.health
    new_is_sick = state.is_sick
    
    # Шанс заболеть если низкая гигиена или голодный
    if not state.is_sick and (new_hygiene < 20 or new_hunger < 10):
        if random.random() < 0.1:  # 10% шанс за тик
            new_is_sick = True
            new_health = clamp(state.health - 10)
    
    # Если болеет - здоровье падает
    if new_is_sick:
        health_loss = int(dt // 1800)  # -1 каждые 30 мин
        new_health = clamp(state.health - health_loss)
        new_happiness = clamp(new_happiness - 5)
    
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