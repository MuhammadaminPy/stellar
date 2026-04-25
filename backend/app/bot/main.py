import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from app.core.config import settings
from app.db.redis import init_redis, redis_client
from app.bot.handlers import user, admin
from app.bot.middlewares import DbSessionMiddleware


async def main():
    await init_redis()

    storage = RedisStorage.from_url(settings.REDIS_URL)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(user.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
