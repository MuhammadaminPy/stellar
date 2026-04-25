import hashlib
import hmac
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote, parse_qsl

from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.user_service import get_or_create_user, get_user_by_tg_id
from app.models import User

# ─── JWT ────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 90  # токен живёт 90 дней

_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(tg_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(tg_id), "exp": expire},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        tg_id = payload.get("sub")
        return int(tg_id) if tg_id else None
    except (JWTError, ValueError, TypeError):
        return None


# ─── Telegram init data verification ────────────────────────────
def verify_telegram_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = parsed.pop("hash", "")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, hash_value):
        raise HTTPException(status_code=401, detail="Invalid Telegram auth")

    user_data = parsed.get("user", "{}")
    return json.loads(unquote(user_data))


# ─── Dependency: get current user (JWT Bearer OR x-init-data) ───
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    x_init_data: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Принимает авторизацию двумя способами:
    1. Authorization: Bearer <jwt_token>   ← фронтенд (после /api/auth/telegram)
    2. x-init-data: <telegram_init_data>  ← прямые запросы / fallback
    """
    # ── Способ 1: JWT Bearer ──────────────────────────────────────
    if credentials and credentials.scheme.lower() == "bearer":
        tg_id = decode_access_token(credentials.credentials)
        if tg_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = await get_user_by_tg_id(db, tg_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    # ── Способ 2: x-init-data header ─────────────────────────────
    if x_init_data:
        tg_user = verify_telegram_init_data(x_init_data)
        tg_id = tg_user.get("id")
        if not tg_id:
            raise HTTPException(status_code=401, detail="No user id in init data")

        username = tg_user.get("username")
        first = tg_user.get("first_name", "")
        last = tg_user.get("last_name", "")
        full_name = f"{first} {last}".strip()

        user, _ = await get_or_create_user(db, tg_id, username, full_name)
        return user

    raise HTTPException(status_code=401, detail="Authorization required")


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.tg_id not in settings.admin_ids_list:
        raise HTTPException(status_code=403, detail="Not admin")
    return current_user
