from sqlalchemy import String, Numeric, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base
from decimal import Decimal
from datetime import datetime
import enum


class ItemType(str, enum.Enum):
    sofa = "sofa"
    window = "window"
    sill = "sill"
    flowers = "flowers"
    character = "character"
    carpet = "carpet"
    wallpaper = "wallpaper"
    pet = "pet"


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    item_type: Mapped[ItemType] = mapped_column(SAEnum(ItemType), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(512))
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sold_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inventories: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="item")
    instances: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="item")


class InventoryItem(Base):
    """
    Конкретный экземпляр предмета с уникальным serial_uid.
    Пример: предмет id=1 (диван-в1), stock=100
      -> экземпляры serial_uid: "1.001", "1.002", ..., "1.100"
    При покупке — inventory_id привязывается к записи Inventory.
    """
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    serial_uid: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    serial_number: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("inventories.id"), nullable=True)

    item: Mapped["Item"] = relationship("Item", back_populates="instances")