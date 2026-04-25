from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models import User
from app.models.transaction import Room, RoomLike
from app.models.pet import Pet

router = APIRouter(prefix="/neighbors", tags=["neighbors"])


@router.get("")
async def list_neighbors(
    sort_by: str = Query("likes", enum=["likes", "pet_level"]),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    per_page = 10
    offset = (page - 1) * per_page

    if sort_by == "pet_level":
        # Join with pets, sort by pet level desc
        stmt = (
            select(
                Room.id.label("room_id"),
                User.full_name.label("owner_name"),
                User.username,
                Room.likes_count,
                Pet.level.label("pet_level"),
                Pet.pet_type.label("pet_type"),
            )
            .join(User, User.tg_id == Room.user_id)
            .outerjoin(Pet, Pet.user_id == Room.user_id)
            .where(Room.user_id != user.tg_id)
            .order_by(Pet.level.desc().nulls_last(), Room.likes_count.desc())
            .offset(offset)
            .limit(per_page)
        )
    else:
        stmt = (
            select(
                Room.id.label("room_id"),
                User.full_name.label("owner_name"),
                User.username,
                Room.likes_count,
                Pet.level.label("pet_level"),
                Pet.pet_type.label("pet_type"),
            )
            .join(User, User.tg_id == Room.user_id)
            .outerjoin(Pet, Pet.user_id == Room.user_id)
            .where(Room.user_id != user.tg_id)
            .order_by(Room.likes_count.desc())
            .offset(offset)
            .limit(per_page)
        )

    result = await db.execute(stmt)
    rows = result.all()

    count_result = await db.execute(
        select(func.count()).select_from(Room).where(Room.user_id != user.tg_id)
    )
    total = count_result.scalar_one()

    PET_EMOJI = {"cat": "🐱", "dog": "🐶"}

    return {
        "rooms": [
            {
                "room_id": row.room_id,
                "owner_name": row.owner_name or row.username or "Игрок",
                "likes_count": row.likes_count,
                "pet_level": row.pet_level,
                "pet_type": row.pet_type,
                "pet_emoji": PET_EMOJI.get(row.pet_type or "", "🏠"),
            }
            for row in rows
        ],
        "total": total,
    }
