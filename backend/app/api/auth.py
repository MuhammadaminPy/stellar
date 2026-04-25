from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import verify_telegram_init_data, create_access_token
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    init_data: str


@router.post("/telegram")
async def auth_telegram(
    body: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Обменивает Telegram WebApp initData на JWT access_token.
    Фронтенд вызывает это при первом открытии.
    """
    try:
        tg_user = verify_telegram_init_data(body.init_data)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid Telegram init data")

    tg_id = tg_user.get("id")
    if not tg_id:
        raise HTTPException(status_code=401, detail="No user id in init data")

    username = tg_user.get("username")
    first = tg_user.get("first_name", "")
    last = tg_user.get("last_name", "")
    full_name = f"{first} {last}".strip()

    user, is_new = await get_or_create_user(db, tg_id, username, full_name)

    access_token = create_access_token(tg_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tg_id": user.tg_id,
        "username": user.username,
        "full_name": user.full_name,
        "is_new": is_new,
        "has_chosen_pet": user.has_chosen_pet,
    }
