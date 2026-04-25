from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.transaction import Transaction, Inventory, Room
    from app.models.pet import Pet


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    referrer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    total_deposited: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    total_withdrawn: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    ref_percent: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    ref_code: Mapped[str | None] = mapped_column(String(12), nullable=True, unique=True, index=True)
    ref_code_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_chosen_pet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    room_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")
    inventory: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="user")
    room: Mapped["Room | None"] = relationship(
        "Room",
        back_populates="owner",
        foreign_keys="Room.user_id",
        uselist=False,
    )
    pet: Mapped["Pet | None"] = relationship("Pet", back_populates="owner", uselist=False)
    referrals: Mapped[list["User"]] = relationship(
        "User",
        primaryjoin="User.tg_id == User.referrer_id",
        foreign_keys="User.referrer_id",
        uselist=True,
    )
