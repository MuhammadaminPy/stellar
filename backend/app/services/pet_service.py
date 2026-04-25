from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models.pet import Pet
from app.models import User, Transaction, TransactionType, TransactionStatus
from app.core.config import settings
from decimal import Decimal


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _xp_for_level_up(level: int) -> int:
    return level * 100


def _add_xp(pet: Pet, amount: int) -> None:
    """Add XP and level up if needed"""
    pet.xp += amount
    while pet.xp >= _xp_for_level_up(pet.level):
        pet.xp -= _xp_for_level_up(pet.level)
        pet.level += 1


async def create_pet(db: AsyncSession, user_id: int, pet_type: str) -> Pet:
    """Create a new pet for a user"""
    now = _now()
    pet = Pet(
        user_id=user_id,
        pet_type=pet_type,
        level=1,
        xp=0,
        is_alive=True,
        last_fed_at=now,
        last_petted_at=now,
        missed_feeds=0,
        missed_pets=0,
        total_feeds=0,
        total_pets=0,
    )
    db.add(pet)
    await db.flush()
    return pet


async def get_pet(db: AsyncSession, user_id: int) -> Pet | None:
    result = await db.execute(select(Pet).where(Pet.user_id == user_id))
    return result.scalar_one_or_none()


def can_feed(pet: Pet) -> tuple[bool, int]:
    """Check if pet can be fed. Returns (can_feed, seconds_remaining)"""
    if not pet.is_alive:
        return False, 0
    if pet.last_fed_at is None:
        return True, 0
    interval = timedelta(hours=settings.PET_FEED_INTERVAL_HOURS)
    next_feed = pet.last_fed_at + interval
    now = _now()
    if now >= next_feed:
        return True, 0
    remaining = int((next_feed - now).total_seconds())
    return False, remaining


def can_pet(pet: Pet) -> tuple[bool, int]:
    """Check if pet can be petted. Returns (can_pet, seconds_remaining)"""
    if not pet.is_alive:
        return False, 0
    if pet.last_petted_at is None:
        return True, 0
    interval = timedelta(hours=settings.PET_PET_INTERVAL_HOURS)
    next_pet = pet.last_petted_at + interval
    now = _now()
    if now >= next_pet:
        return True, 0
    remaining = int((next_pet - now).total_seconds())
    return False, remaining


async def feed_pet(
    db: AsyncSession,
    user: User,
    pet: Pet,
    bulk: bool = False,
) -> dict:
    """Feed a pet. Deducts tokens from user balance."""
    if not pet.is_alive:
        raise ValueError("Питомец погиб. Нужно начать заново.")

    ok, remaining = can_feed(pet)
    if not ok:
        raise ValueError(f"Ещё рано кормить. Осталось: {remaining // 60} мин.")

    price = Decimal(str(settings.PET_FEED_BULK_PRICE if bulk else settings.PET_FEED_PRICE))
    if user.balance < price:
        raise ValueError(f"Недостаточно средств. Нужно {price} $DF")

    user.balance -= price
    await db.flush()

    # Create transaction
    tx = Transaction(
        user_id=user.tg_id,
        tx_type=TransactionType.pet_feed,
        amount=price,
        status=TransactionStatus.completed,
        note=f"Корм питомца ({'bulk' if bulk else 'single'})",
    )
    db.add(tx)

    now = _now()
    pet.last_fed_at = now
    pet.missed_feeds = 0
    pet.total_feeds += 1
    _add_xp(pet, 10 if not bulk else 50)

    await db.flush()
    return {
        "success": True,
        "xp_gained": 10 if not bulk else 50,
        "level": pet.level,
        "xp": pet.xp,
        "charged": str(price),
    }


async def pet_the_pet(
    db: AsyncSession,
    user_id: int,
    pet: Pet,
) -> dict:
    """Pet the pet (free action)."""
    if not pet.is_alive:
        raise ValueError("Питомец погиб.")

    ok, remaining = can_pet(pet)
    if not ok:
        raise ValueError(f"Ещё рано гладить. Осталось: {remaining // 60} мин.")

    now = _now()
    pet.last_petted_at = now
    pet.missed_pets = 0
    pet.total_pets += 1
    _add_xp(pet, 5)

    await db.flush()
    return {
        "success": True,
        "xp_gained": 5,
        "level": pet.level,
        "xp": pet.xp,
    }


async def check_pet_health(db: AsyncSession, pet: Pet) -> None:
    """Check if pet should die due to missed actions. Call periodically."""
    if not pet.is_alive:
        return

    now = _now()
    feed_interval = timedelta(hours=settings.PET_FEED_INTERVAL_HOURS)
    pet_interval = timedelta(hours=settings.PET_PET_INTERVAL_HOURS)
    limit = settings.PET_MISS_LIMIT

    # Check missed feeds
    if pet.last_fed_at and (now - pet.last_fed_at) > feed_interval * (limit + 1):
        pet.is_alive = False
        await db.flush()
        return

    # Check missed pets
    if pet.last_petted_at and (now - pet.last_petted_at) > pet_interval * (limit + 1):
        pet.is_alive = False
        await db.flush()
        return


def pet_to_dict(pet: Pet) -> dict:
    now = _now()
    feed_ok, feed_wait = can_feed(pet)
    pet_ok, pet_wait = can_pet(pet)

    # Calculate next feed/pet time
    next_feed_at = None
    if pet.last_fed_at:
        next_feed_at = (pet.last_fed_at + timedelta(hours=settings.PET_FEED_INTERVAL_HOURS)).isoformat()
    next_pet_at = None
    if pet.last_petted_at:
        next_pet_at = (pet.last_petted_at + timedelta(hours=settings.PET_PET_INTERVAL_HOURS)).isoformat()

    return {
        "id": pet.id,
        "pet_type": pet.pet_type,
        "name": pet.name,
        "level": pet.level,
        "xp": pet.xp,
        "xp_for_next": _xp_for_level_up(pet.level),
        "is_alive": pet.is_alive,
        "can_feed": feed_ok,
        "feed_wait_seconds": feed_wait,
        "can_pet": pet_ok,
        "pet_wait_seconds": pet_wait,
        "total_feeds": pet.total_feeds,
        "total_pets": pet.total_pets,
        "next_feed_at": next_feed_at,
        "next_pet_at": next_pet_at,
        "feed_price": settings.PET_FEED_PRICE,
        "feed_bulk_price": settings.PET_FEED_BULK_PRICE,
        "feed_bulk_hours": settings.PET_FEED_BULK_HOURS,
    }
