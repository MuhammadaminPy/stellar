import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def init_redis():
    global redis_client
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        # retry при разрыве соединения
        retry_on_timeout=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
    )


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
