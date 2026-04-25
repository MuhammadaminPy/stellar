from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal
from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.config import settings
from app.models import User
from app.services.user_service import (
    process_deposit,
    create_withdraw_request,
    get_referrals_count,
    get_referral_earnings,
    get_user_by_ref_code,
    activate_user_by_ref_code,
)
from app.services.ton_service import find_deposit_by_comment

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ref_count = await get_referrals_count(db, user.tg_id)
    ref_earnings = await get_referral_earnings(db, user.tg_id)

    return {
        "tg_id": user.tg_id,
        "username": user.username,
        "full_name": user.full_name,
        "balance": str(user.balance),
        "total_deposited": str(user.total_deposited),
        "total_withdrawn": str(user.total_withdrawn),
        "room_id": user.room_id,
        "ref_code": user.ref_code,
        "ref_count": ref_count,
        "ref_earnings": str(ref_earnings),
        "ref_code_used": user.ref_code_used,
        "created_at": user.created_at.isoformat(),
    }


class DepositCheckRequest(BaseModel):
    amount: Decimal
    comment: str


@router.post("/deposit/check")
async def check_deposit(
    body: DepositCheckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    min_nano = int(body.amount * Decimal("1e9"))
    tx = await find_deposit_by_comment(body.comment, min_nano)
    if not tx:
        return {"found": False}

    result = await process_deposit(
        db,
        user,
        Decimal(str(tx["amount_ton"])),
        tx["hash"],
        body.comment,
    )
    return {
        "found": True,
        "credited": str(result.amount),
        "tx_id": result.id,
    }


class TonDepositRequest(BaseModel):
    """Deposit confirmed via TonConnect transaction"""
    boc: str          # Transaction BOC (from TonConnect)
    amount_ton: Decimal
    wallet_address: str


@router.post("/deposit/ton_connect")
async def deposit_via_ton_connect(
    body: TonDepositRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a deposit confirmed via TonConnect"""
    from app.services.ton_service import verify_ton_connect_tx
    comment = f"DF{user.tg_id}"

    tx_hash = await verify_ton_connect_tx(body.boc, body.wallet_address, comment, body.amount_ton)
    if not tx_hash:
        raise HTTPException(status_code=400, detail="Транзакция не подтверждена. Попробуйте позже.")

    result = await process_deposit(db, user, body.amount_ton, tx_hash, comment)
    return {
        "success": True,
        "credited": str(result.amount),
        "tx_id": result.id,
    }


@router.get("/deposit/info")
async def deposit_info(user: User = Depends(get_current_user)):
    comment = f"DF{user.tg_id}"
    return {
        "wallet": settings.TON_WALLET_ADDRESS,
        "comment": comment,
        "token_address": settings.DF_TOKEN_ADDRESS,
        "bonus_percent": settings.DEPOSIT_BONUS_PERCENT,
    }


class WithdrawRequest(BaseModel):
    amount: Decimal
    wallet_address: str


@router.post("/withdraw")
async def withdraw(
    body: WithdrawRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")
    try:
        tx = await create_withdraw_request(db, user, body.amount, body.wallet_address)
        return {"success": True, "tx_id": tx.id, "amount": str(tx.amount)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────── ROOM POSITIONS ───────────────────

class SaveRoomPositionsRequest(BaseModel):
    positions: dict  # {item_type: {x, y, w, h}}


@router.post("/room/positions")
async def save_room_positions(
    body: SaveRoomPositionsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Room
    import json

    result = await db.execute(select(Room).where(Room.user_id == user.tg_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")

    room.item_positions = json.dumps(body.positions)
    await db.flush()
    return {"success": True}


@router.get("/room/positions")
async def get_room_positions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Room
    import json

    result = await db.execute(select(Room).where(Room.user_id == user.tg_id))
    room = result.scalar_one_or_none()
    if not room or not room.item_positions:
        return {"positions": None}

    return {"positions": json.loads(room.item_positions)}


class ActivateRefRequest(BaseModel):
    ref_code: str


@router.post("/activate_ref")
async def activate_ref(
    body: ActivateRefRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    if user.ref_code_used:
        return {"success": True, "already_activated": True}

    success = await activate_user_by_ref_code(db, user, body.ref_code)
    if not success:
        raise HTTPException(status_code=400, detail="Неверный или несуществующий реф код")

    return {"success": True}


@router.get("/transactions")
async def get_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, desc
    from app.models import Transaction
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.tg_id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    txs = result.scalars().all()
    return {
        "transactions": [
            {
                "id": tx.id,
                "tx_type": tx.tx_type.value,
                "amount": str(tx.amount),
                "status": tx.status.value,
                "created_at": tx.created_at.isoformat(),
                "note": tx.note,
            }
            for tx in txs
        ]
    }
