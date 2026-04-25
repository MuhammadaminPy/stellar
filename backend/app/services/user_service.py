import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import User, Transaction, TransactionType, TransactionStatus, Room
from app.core.config import settings
from decimal import Decimal


def generate_ref_code() -> str:
    """Generate unique 8-char uppercase alphanumeric ref code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


async def create_unique_ref_code(db: AsyncSession) -> str:
    """Generate a ref code guaranteed to be unique in DB"""
    for _ in range(10):
        code = generate_ref_code()
        result = await db.execute(select(User).where(User.ref_code == code))
        if not result.scalar_one_or_none():
            return code
    # Fallback: longer code
    return generate_ref_code() + secrets.token_hex(2).upper()


async def get_or_create_user(
    db: AsyncSession,
    tg_id: int,
    username: str | None,
    full_name: str | None,
    referrer_tg_id: int | None = None,
) -> tuple[User, bool]:
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        user.username = username
        user.full_name = full_name
        await db.flush()
        return user, False

    referrer_id = None
    if referrer_tg_id and referrer_tg_id != tg_id:
        ref_result = await db.execute(select(User).where(User.tg_id == referrer_tg_id))
        ref_user = ref_result.scalar_one_or_none()
        if ref_user:
            referrer_id = referrer_tg_id

    ref_code = await create_unique_ref_code(db)

    user = User(
        tg_id=tg_id,
        username=username,
        full_name=full_name,
        referrer_id=referrer_id,
        ref_percent=settings.DEFAULT_REF_PERCENT,
        ref_code=ref_code,
        ref_code_used=(referrer_id is not None),  # if has referrer, already valid
    )
    db.add(user)
    await db.flush()

    room = Room(user_id=tg_id)
    db.add(room)
    await db.flush()

    user.room_id = room.id
    await db.flush()

    return user, True


async def get_user_by_tg_id(db: AsyncSession, tg_id: int) -> User | None:
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_ref_code(db: AsyncSession, ref_code: str) -> User | None:
    result = await db.execute(select(User).where(User.ref_code == ref_code.upper()))
    return result.scalar_one_or_none()


async def activate_user_by_ref_code(
    db: AsyncSession,
    user: User,
    ref_code: str,
) -> bool:
    """Activate a user with a valid ref code. Returns True if successful."""
    if user.ref_code_used:
        return True  # Already activated

    referrer = await get_user_by_ref_code(db, ref_code)
    if not referrer or referrer.tg_id == user.tg_id:
        return False

    user.referrer_id = referrer.tg_id
    user.ref_code_used = True
    await db.flush()
    return True


async def get_active_users_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def adjust_balance(db: AsyncSession, tg_id: int, amount: Decimal) -> User:
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one()
    user.balance += amount
    await db.flush()
    return user


async def process_deposit(
    db: AsyncSession,
    user: User,
    amount: Decimal,
    ton_tx_hash: str,
    comment: str,
) -> Transaction:
    bonus_percent = settings.DEPOSIT_BONUS_PERCENT
    credited = amount * Decimal(1 + bonus_percent / 100)

    user.balance += credited
    user.total_deposited += credited
    await db.flush()

    tx = Transaction(
        user_id=user.tg_id,
        tx_type=TransactionType.deposit,
        amount=credited,
        status=TransactionStatus.completed,
        ton_tx_hash=ton_tx_hash,
        comment=comment,
    )
    db.add(tx)
    await db.flush()

    if user.referrer_id:
        ref_result = await db.execute(select(User).where(User.tg_id == user.referrer_id))
        referrer = ref_result.scalar_one_or_none()
        if referrer:
            ref_bonus = credited * Decimal(referrer.ref_percent) / Decimal(100)
            referrer.balance += ref_bonus
            ref_tx = Transaction(
                user_id=referrer.tg_id,
                tx_type=TransactionType.referral_bonus,
                amount=ref_bonus,
                status=TransactionStatus.completed,
                note=f"Реферал {user.tg_id}",
            )
            db.add(ref_tx)
            await db.flush()

    return tx


async def create_withdraw_request(
    db: AsyncSession,
    user: User,
    amount: Decimal,
    wallet_address: str,
) -> Transaction:
    if user.balance < amount:
        raise ValueError("Недостаточно средств")

    user.balance -= amount
    await db.flush()

    tx = Transaction(
        user_id=user.tg_id,
        tx_type=TransactionType.withdraw,
        amount=amount,
        status=TransactionStatus.pending,
        wallet_address=wallet_address,
    )
    db.add(tx)
    await db.flush()
    return tx


async def get_referrals_count(db: AsyncSession, tg_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(User).where(User.referrer_id == tg_id)
    )
    return result.scalar_one()


async def get_referral_earnings(db: AsyncSession, tg_id: int) -> Decimal:
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == tg_id,
            Transaction.tx_type == TransactionType.referral_bonus,
            Transaction.status == TransactionStatus.completed,
        )
    )
    return result.scalar_one()
