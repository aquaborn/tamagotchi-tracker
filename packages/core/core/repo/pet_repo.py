from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.pet import PetModel
from packages.core.core.domain.pet import PetState

class PetRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Optional[PetState]:
        result = await self.session.execute(
            select(PetModel).where(PetModel.user_id == user_id)
        )
        pet = result.scalar_one_or_none()
        if not pet:
            return None
        
        return PetState(
            hunger=pet.hunger,
            energy=pet.energy,
            happiness=pet.happiness,
            hygiene=getattr(pet, 'hygiene', 100),
            health=getattr(pet, 'health', 100),
            discipline=getattr(pet, 'discipline', 50),
            is_sick=getattr(pet, 'is_sick', False),
            is_sleeping=getattr(pet, 'is_sleeping', False),
            light_off=getattr(pet, 'light_off', False),
            last_tick_at=pet.last_tick_at
        )

    async def create_for_user(self, user_id: int, state: PetState) -> PetState:
        pet = PetModel(
            user_id=user_id,
            hunger=state.hunger,
            energy=state.energy,
            happiness=state.happiness,
            hygiene=state.hygiene,
            health=state.health,
            discipline=state.discipline,
            is_sick=state.is_sick,
            is_sleeping=state.is_sleeping,
            light_off=state.light_off,
            last_tick_at=state.last_tick_at
        )
        self.session.add(pet)
        await self.session.commit()
        await self.session.refresh(pet)
        return state

    async def update(self, user_id: int, state: PetState) -> PetState:
        result = await self.session.execute(
            select(PetModel).where(PetModel.user_id == user_id)
        )
        pet = result.scalar_one_or_none()
        if not pet:
            return await self.create_for_user(user_id, state)
        
        pet.hunger = state.hunger
        pet.energy = state.energy
        pet.happiness = state.happiness
        pet.hygiene = state.hygiene
        pet.health = state.health
        pet.discipline = state.discipline
        pet.is_sick = state.is_sick
        pet.is_sleeping = state.is_sleeping
        pet.light_off = state.light_off
        pet.last_tick_at = state.last_tick_at
        
        await self.session.commit()
        await self.session.refresh(pet)
        return state