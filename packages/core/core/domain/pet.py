from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class PetState:
    hunger: int       # 0..100 (100 = сытый)
    energy: int       # 0..100
    happiness: int    # 0..100
    last_tick_at: datetime

def clamp(v: int) -> int:
    return max(0, min(100, v))

def apply_tick(state: PetState, now: datetime) -> PetState:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    dt = (now - state.last_tick_at).total_seconds()
    if dt <= 0:
        return state

    # Простейшая деградация: каждые 10 минут -1 сытости, каждые 15 минут -1 энергии
    hunger_loss = int(dt // 600)
    energy_loss = int(dt // 900)

    return PetState(
        hunger=clamp(state.hunger - hunger_loss),
        energy=clamp(state.energy - energy_loss),
        happiness=clamp(state.happiness - (1 if state.hunger < 20 else 0)),
        last_tick_at=now,
    )