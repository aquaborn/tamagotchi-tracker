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
            last_tick_at=pet.last_tick_at
        )

    async def create_for_user(self, user_id: int, state: PetState) -> PetState:
        pet = PetModel(
            user_id=user_id,
            hunger=state.hunger,
            energy=state.energy,
            happiness=state.happiness,
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
        pet.last_tick_at = state.last_tick_at
        
        await self.session.commit()
        await self.session.refresh(pet)
        return state