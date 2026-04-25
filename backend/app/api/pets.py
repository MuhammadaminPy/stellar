from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models import User
from app.services.pet_service import (
    get_pet,
    create_pet,
    feed_pet,
    pet_the_pet,
    check_pet_health,
    pet_to_dict,
)

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("/me")
async def get_my_pet(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pet = await get_pet(db, user.tg_id)
    if not pet:
        return {"has_pet": False, "pet": None, "has_chosen_pet": user.has_chosen_pet}

    await check_pet_health(db, pet)
    return {"has_pet": True, "pet": pet_to_dict(pet), "has_chosen_pet": user.has_chosen_pet}


class ChoosePetRequest(BaseModel):
    pet_type: str  # 'cat' or 'dog'


@router.post("/choose")
async def choose_pet(
    body: ChoosePetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.pet_type not in ("cat", "dog"):
        raise HTTPException(status_code=400, detail="Тип питомца: 'cat' или 'dog'")

    existing = await get_pet(db, user.tg_id)
    if existing:
        raise HTTPException(status_code=400, detail="Питомец уже выбран")

    pet = await create_pet(db, user.tg_id, body.pet_type)
    user.has_chosen_pet = True
    await db.flush()

    return {"success": True, "pet": pet_to_dict(pet)}


@router.post("/feed")
async def feed(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pet = await get_pet(db, user.tg_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    try:
        result = await feed_pet(db, user, pet, bulk=False)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feed_bulk")
async def feed_bulk(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pet = await get_pet(db, user.tg_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    try:
        result = await feed_pet(db, user, pet, bulk=True)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pet")
async def pet_action(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pet = await get_pet(db, user.tg_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    try:
        result = await pet_the_pet(db, user.tg_id, pet)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
