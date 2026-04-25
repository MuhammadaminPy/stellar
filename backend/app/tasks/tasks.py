import asyncio
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.redis import init_redis, redis_client
from app.services.dex_service import get_token_stats
import json


@celery_app.task(name="app.tasks.tasks.cache_dex_stats")
def cache_dex_stats():
    async def _run():
        await init_redis()
        stats = await get_token_stats()
        await redis_client.setex("info:dex_stats", 60, json.dumps(stats))
    asyncio.run(_run())


@celery_app.task(name="app.tasks.tasks.check_pending_deposits")
def check_pending_deposits():
    async def _run():
        from sqlalchemy import select
        from app.models import Transaction, TransactionStatus, TransactionType, User
        from app.services.ton_service import find_deposit_by_comment
        from app.services.user_service import process_deposit
        from decimal import Decimal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Transaction).where(
                    Transaction.tx_type == TransactionType.deposit,
                    Transaction.status == TransactionStatus.pending,
                )
            )
            pending = result.scalars().all()

            for tx in pending:
                if not tx.comment:
                    continue
                found = await find_deposit_by_comment(tx.comment)
                if found:
                    user_result = await db.execute(
                        select(User).where(User.tg_id == tx.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user:
                        await process_deposit(
                            db, user, Decimal(str(found["amount_ton"])),
                            found["hash"], tx.comment,
                        )
                        tx.status = TransactionStatus.completed
            await db.commit()

    asyncio.run(_run())
