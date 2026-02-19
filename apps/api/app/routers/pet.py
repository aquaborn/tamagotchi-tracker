from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import get_current_user_id
from app.deps.db import get_db
from packages.core.core.domain.pet import apply_tick, PetState, clamp
from packages.core.core.repo.pet_repo import PetRepo

router = APIRouter(prefix="/v1/pet", tags=["pet"])

@router.get("/state")
async def get_state(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepo(db)
    state = await pet_repo.get_by_user_id(user_id)
    
    if not state:
        # Create default pet state
        now = datetime.now(timezone.utc)
        state = PetState(hunger=100, energy=100, happiness=100, last_tick_at=now)
        state = await pet_repo.create_for_user(user_id, state)
    
    # Apply time-based degradation
    now = datetime.now(timezone.utc)
    updated_state = apply_tick(state, now)
    
    # Save updated state
    await pet_repo.update(user_id, updated_state)
    
    return {
        "pet": {
            "hunger": updated_state.hunger,
            "energy": updated_state.energy,
            "happiness": updated_state.happiness,
        },
        "server_time": now.isoformat(),
        "last_activity": updated_state.last_tick_at.isoformat()
    }

@router.post("/action")
async def perform_action(
    action: str,
    item_id: str = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepo(db)
    state = await pet_repo.get_by_user_id(user_id)
    
    if not state:
        now = datetime.now(timezone.utc)
        state = PetState(hunger=100, energy=100, happiness=100, last_tick_at=now)
        state = await pet_repo.create_for_user(user_id, state)
    
    # Apply time-based degradation first
    now = datetime.now(timezone.utc)
    state = apply_tick(state, now)
    
    # Apply action
    if action == "feed":
        state = PetState(
            hunger=clamp(state.hunger + 20),
            energy=state.energy,
            happiness=clamp(state.happiness + 5),
            last_tick_at=now
        )
    elif action == "play":
        state = PetState(
            hunger=clamp(state.hunger - 10),
            energy=clamp(state.energy - 15),
            happiness=clamp(state.happiness + 15),
            last_tick_at=now
        )
    elif action == "sleep":
        state = PetState(
            hunger=state.hunger,
            energy=clamp(state.energy + 30),
            happiness=clamp(state.happiness + 10),
            last_tick_at=now
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # Save updated state
    await pet_repo.update(user_id, state)
    
    return {
        "pet": {
            "hunger": state.hunger,
            "energy": state.energy,
            "happiness": state.happiness,
        },
        "server_time": now.isoformat()
    }

@router.post("/auth/session")
async def create_session(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    # This endpoint exists just to trigger the JWT creation flow
    # The actual JWT is returned by the dependency
    return {"message": "Session created"}