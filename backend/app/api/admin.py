from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.db.session import get_db
from app.core.auth import get_current_admin
from app.core.config import settings
from app.models import User, Transaction, TransactionType, TransactionStatus, Inventory
from app.models.item import Item, ItemType, InventoryItem
from app.services.shop_service import create_item, find_item_owner, find_item_instances, get_item_by_id, get_item_by_serial_uid

router = APIRouter(prefix="/admin", tags=["admin"])


# ─────────────────── СТАТИСТИКА ───────────────────

@router.get("/stats")
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    new_users = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= day_ago)
    )).scalar_one()
    deposited = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.tx_type == TransactionType.deposit, Transaction.status == TransactionStatus.completed)
    )).scalar_one()
    withdrawn = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.tx_type == TransactionType.withdraw, Transaction.status == TransactionStatus.completed)
    )).scalar_one()

    return {
        "total_users": total_users,
        "new_users_24h": new_users,
        "total_deposited": str(deposited),
        "total_withdrawn": str(withdrawn),
    }


# ─────────────────── ПОЛЬЗОВАТЕЛИ ───────────────────

@router.get("/user/{tg_id}")
async def get_user(
    tg_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "tg_id": user.tg_id,
        "username": user.username,
        "full_name": user.full_name,
        "balance": str(user.balance),
        "total_deposited": str(user.total_deposited),
        "total_withdrawn": str(user.total_withdrawn),
        "ref_percent": user.ref_percent,
        "ref_code": user.ref_code,
        "is_banned": user.is_banned,
        "created_at": user.created_at.isoformat(),
    }


class AdjustBalanceRequest(BaseModel):
    tg_id: int
    amount: Decimal
    note: str = ""


@router.post("/user/adjust_balance")
async def adjust_balance(
    body: AdjustBalanceRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.tg_id == body.tg_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.balance += body.amount
    tx_type = TransactionType.admin_add if body.amount >= 0 else TransactionType.admin_sub
    db.add(Transaction(
        user_id=body.tg_id,
        tx_type=tx_type,
        amount=abs(body.amount),
        status=TransactionStatus.completed,
        note=body.note or f"Корректировка админом {admin.tg_id}",
    ))
    await db.flush()
    return {"success": True, "new_balance": str(user.balance)}


class SetRefPercentRequest(BaseModel):
    tg_id: int
    ref_percent: int


@router.post("/user/set_ref_percent")
async def set_ref_percent(
    body: SetRefPercentRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.tg_id == body.tg_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.ref_percent = body.ref_percent
    await db.flush()
    return {"success": True, "ref_percent": user.ref_percent}


# ─────────────────── ВЫВОД СРЕДСТВ ───────────────────

@router.get("/withdrawals")
async def get_pending_withdrawals(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.tx_type == TransactionType.withdraw,
            Transaction.status == TransactionStatus.pending,
        ).limit(50)
    )
    txs = result.scalars().all()
    return [
        {
            "id": tx.id,
            "user_id": tx.user_id,
            "amount": str(tx.amount),
            "wallet_address": tx.wallet_address,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in txs
    ]


class WithdrawalActionRequest(BaseModel):
    tx_id: int
    action: str  # "approve" or "reject"


@router.post("/withdrawals/action")
async def withdrawal_action(
    body: WithdrawalActionRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action должен быть 'approve' или 'reject'")

    result = await db.execute(select(Transaction).where(Transaction.id == body.tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    if tx.status != TransactionStatus.pending:
        raise HTTPException(status_code=400, detail="Транзакция уже обработана")

    user_result = await db.execute(select(User).where(User.tg_id == tx.user_id))
    user = user_result.scalar_one()

    if body.action == "approve":
        tx.status = TransactionStatus.completed
        user.total_withdrawn += tx.amount
    else:
        tx.status = TransactionStatus.rejected
        user.balance += tx.amount

    await db.flush()
    return {"success": True, "tx_id": tx.id, "status": tx.status.value}


# ─────────────────── ТОВАРЫ ───────────────────

class AddItemRequest(BaseModel):
    name: str
    description: str | None = None
    item_type: str
    price: Decimal
    photo_url: str | None = None
    stock: int | None = None


@router.post("/items/add")
async def add_item(
    body: AddItemRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        item_type = ItemType(body.item_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный тип товара: {body.item_type}")

    item = await create_item(
        db,
        name=body.name,
        description=body.description,
        item_type=item_type,
        price=body.price,
        photo_url=body.photo_url,
        stock=body.stock,
    )
    return {"success": True, "item_id": item.id}


@router.get("/items/{item_id}")
async def find_item(
    item_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    owners = await find_item_owner(db, item_id)
    instances = await find_item_instances(db, item_id)
    sold = len([i for i in instances if i.inventory_id is not None])
    free = len([i for i in instances if i.inventory_id is None])

    return {
        "id": item.id,
        "name": item.name,
        "item_type": item.item_type.value,
        "price": str(item.price),
        "stock": item.stock,
        "sold_count": item.sold_count,
        "is_active": item.is_active,
        "instances_total": len(instances),
        "instances_sold": sold,
        "instances_free": free,
        "owners": [{"user_id": o.user_id, "bought_at": o.bought_at.isoformat()} for o in owners[:20]],
    }


@router.get("/items/serial/{serial_uid}")
async def find_item_by_serial(
    serial_uid: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    instance = await get_item_by_serial_uid(db, serial_uid)
    if not instance:
        raise HTTPException(status_code=404, detail="Экземпляр не найден")

    owner = None
    if instance.inventory_id:
        inv_result = await db.execute(select(Inventory).where(Inventory.id == instance.inventory_id))
        inv = inv_result.scalar_one_or_none()
        if inv:
            owner = {"user_id": inv.user_id, "bought_at": inv.bought_at.isoformat()}

    return {
        "serial_uid": instance.serial_uid,
        "serial_number": instance.serial_number,
        "item_id": instance.item_id,
        "item_name": instance.item.name,
        "owner": owner,
    }


# ─────────────────── БОНУС ───────────────────

class SetBonusRequest(BaseModel):
    percent: int


@router.post("/set_bonus")
async def set_bonus(
    body: SetBonusRequest,
    admin: User = Depends(get_current_admin),
):
    settings.DEPOSIT_BONUS_PERCENT = body.percent
    return {"success": True, "deposit_bonus_percent": settings.DEPOSIT_BONUS_PERCENT}


# ─────────────────── ТОП РЕФОВОДОВ (ИСПРАВЛЕН) ───────────────────

@router.get("/top_refs")
async def top_refs(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Use aliased self-join to count referrals correctly
    Referral = aliased(User, name="referral")
    result = await db.execute(
        select(
            User.tg_id,
            User.full_name,
            User.username,
            User.ref_code,
            func.count(Referral.tg_id).label("ref_count"),
        )
        .outerjoin(Referral, Referral.referrer_id == User.tg_id)
        .group_by(User.tg_id, User.full_name, User.username, User.ref_code)
        .order_by(func.count(Referral.tg_id).desc())
        .limit(20)
    )
    rows = result.all()
    return [
        {
            "tg_id": row.tg_id,
            "full_name": row.full_name,
            "username": row.username,
            "ref_code": row.ref_code,
            "ref_count": row.ref_count,
        }
        for row in rows
        if row.ref_count > 0
    ]


# ─────────────────── НАСТРОЙКИ ПИТОМЦА ───────────────────

class PetSettingsRequest(BaseModel):
    feed_interval_hours: int | None = None
    pet_interval_hours: int | None = None
    feed_price: float | None = None
    feed_bulk_hours: int | None = None
    feed_bulk_price: float | None = None
    miss_limit: int | None = None


@router.post("/pet_settings")
async def set_pet_settings(
    body: PetSettingsRequest,
    admin: User = Depends(get_current_admin),
):
    if body.feed_interval_hours is not None:
        settings.PET_FEED_INTERVAL_HOURS = body.feed_interval_hours
    if body.pet_interval_hours is not None:
        settings.PET_PET_INTERVAL_HOURS = body.pet_interval_hours
    if body.feed_price is not None:
        settings.PET_FEED_PRICE = body.feed_price
    if body.feed_bulk_hours is not None:
        settings.PET_FEED_BULK_HOURS = body.feed_bulk_hours
    if body.feed_bulk_price is not None:
        settings.PET_FEED_BULK_PRICE = body.feed_bulk_price
    if body.miss_limit is not None:
        settings.PET_MISS_LIMIT = body.miss_limit

    return {
        "success": True,
        "pet_feed_interval_hours": settings.PET_FEED_INTERVAL_HOURS,
        "pet_pet_interval_hours": settings.PET_PET_INTERVAL_HOURS,
        "pet_feed_price": settings.PET_FEED_PRICE,
        "pet_feed_bulk_hours": settings.PET_FEED_BULK_HOURS,
        "pet_feed_bulk_price": settings.PET_FEED_BULK_PRICE,
        "pet_miss_limit": settings.PET_MISS_LIMIT,
    }


@router.get("/pet_settings")
async def get_pet_settings(
    admin: User = Depends(get_current_admin),
):
    return {
        "pet_feed_interval_hours": settings.PET_FEED_INTERVAL_HOURS,
        "pet_pet_interval_hours": settings.PET_PET_INTERVAL_HOURS,
        "pet_feed_price": settings.PET_FEED_PRICE,
        "pet_feed_bulk_hours": settings.PET_FEED_BULK_HOURS,
        "pet_feed_bulk_price": settings.PET_FEED_BULK_PRICE,
        "pet_miss_limit": settings.PET_MISS_LIMIT,
    }
