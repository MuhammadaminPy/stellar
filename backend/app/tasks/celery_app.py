from celery import Celery
from app.core.config import settings

celery_app = Celery("df_bot", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.beat_schedule = {
    "check-pending-deposits": {
        "task": "app.tasks.tasks.check_pending_deposits",
        "schedule": 60.0,
    },
    "cache-dex-stats": {
        "task": "app.tasks.tasks.cache_dex_stats",
        "schedule": 30.0,
    },
}

celery_app.conf.timezone = "UTC"
