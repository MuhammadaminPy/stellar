from sqlalchemy import BigInteger, Integer, Boolean, DateTime, ForeignKey, Numeric, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base
from decimal import Decimal
from datetime import datetime
import enum


class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    bought_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="inventory")
    item: Mapped["Item"] = relationship("Item", back_populates="inventories")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=False, unique=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    item_positions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of custom positions
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="room", foreign_keys=[user_id])
    likes: Mapped[list["RoomLike"]] = relationship("RoomLike", back_populates="room")


class RoomLike(Base):
    __tablename__ = "room_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    room: Mapped["Room"] = relationship("Room", back_populates="likes")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class TransactionType(str, enum.Enum):
    deposit = "deposit"
    withdraw = "withdraw"
    purchase = "purchase"
    referral_bonus = "referral_bonus"
    admin_add = "admin_add"
    admin_sub = "admin_sub"
    pet_feed = "pet_feed"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    rejected = "rejected"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), nullable=False, index=True)
    tx_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SAEnum(TransactionStatus), default=TransactionStatus.pending, index=True)
    wallet_address: Mapped[str | None] = mapped_column(String(128))
    ton_tx_hash: Mapped[str | None] = mapped_column(String(256))
    comment: Mapped[str | None] = mapped_column(String(256))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="transactions")
