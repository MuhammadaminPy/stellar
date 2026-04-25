from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    REDIS_URL: str

    BOT_TOKEN: str
    ADMIN_IDS: str
    WEBAPP_URL: str
    SECRET_KEY: str

    TON_API_KEY: str
    TON_WALLET_ADDRESS: str
    DF_TOKEN_ADDRESS: str
    DEX_SCREENER_PAIR: str

    DEFAULT_REF_PERCENT: int = 10
    DEPOSIT_BONUS_PERCENT: int = 0

    # Pet settings (configurable by admin)
    PET_FEED_INTERVAL_HOURS: int = 2
    PET_PET_INTERVAL_HOURS: int = 1
    PET_FEED_PRICE: float = 1.0           # 1 $DF per feed
    PET_FEED_BULK_HOURS: int = 10         # Bulk pre-pay for 10 hours
    PET_FEED_BULK_PRICE: float = 9.0      # 9 $DF for 10-hour bulk
    PET_MISS_LIMIT: int = 2               # How many misses before death

    class Config:
        env_file = ".env"

    @property
    def admin_ids_list(self) -> List[int]:
        return [int(i.strip()) for i in self.ADMIN_IDS.split(",")]


settings = Settings()
