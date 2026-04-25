from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=False, unique=True, index=True)
    pet_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'cat' or 'dog'
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_petted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    missed_feeds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missed_pets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_feeds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="pet")

    @property
    def xp_for_next_level(self) -> int:
        """XP needed to reach next level: level * 100"""
        return self.level * 100

    @property
    def level_progress(self) -> float:
        """Progress to next level (0.0 - 1.0)"""
        needed = self.xp_for_next_level
        if needed == 0:
            return 1.0
        return min(1.0, self.xp / needed)
