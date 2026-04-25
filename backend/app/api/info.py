from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.redis import get_redis
from app.services.user_service import get_active_users_count
from app.services.dex_service import get_token_stats
from app.services.ton_service import get_token_holders
from app.core.config import settings
import json

router = APIRouter(prefix="/info", tags=["info"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    cache_key = "info:stats"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    users_count = await get_active_users_count(db)
    dex_stats = await get_token_stats()

    result = {
        "active_users": users_count,
        "token_address": settings.DF_TOKEN_ADDRESS,
        "dex": dex_stats,
    }
    await redis.setex(cache_key, 60, json.dumps(result))
    return result


@router.get("/holders")
async def get_holders(redis=Depends(get_redis)):
    cache_key = "info:holders"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    holders = await get_token_holders(settings.DF_TOKEN_ADDRESS, limit=10)
    await redis.setex(cache_key, 120, json.dumps(holders))
    return {"holders": holders}
