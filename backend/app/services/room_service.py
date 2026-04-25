from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from app.models import Room, RoomLike, User, Inventory


async def get_neighbors(
    db: AsyncSession,
    page: int = 1,
    sort_by: str = "likes",
) -> tuple[list[dict], int]:
    per_page = 5

    has_purchase = (
        select(Inventory.id)
        .where(Inventory.user_id == Room.user_id)
        .correlate(Room)
        .exists()
    )

    count_result = await db.execute(
        select(func.count()).select_from(Room).where(has_purchase)
    )
    total = count_result.scalar_one()

    query = (
        select(Room, User)
        .join(User, User.tg_id == Room.user_id)
        .where(has_purchase)
    )

    if sort_by == "likes_desc":
        query = query.order_by(Room.likes_count.desc())
    elif sort_by == "likes_asc":
        query = query.order_by(Room.likes_count.asc())
    else:
        query = query.order_by(Room.id.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    rows = result.all()

    neighbors = []
    for room, user in rows:
        neighbors.append({
            "room_id": room.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "full_name": user.full_name,
            "likes": room.likes_count,
        })

    return neighbors, total


async def like_room(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    existing = await db.execute(
        select(RoomLike).where(
            RoomLike.room_id == room_id,
            RoomLike.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        return False

    like = RoomLike(room_id=room_id, user_id=user_id)
    db.add(like)

    room_result = await db.execute(select(Room).where(Room.id == room_id))
    room = room_result.scalar_one()
    room.likes_count += 1
    await db.flush()
    return True
