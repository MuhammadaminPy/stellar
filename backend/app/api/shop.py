from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models import User, ItemType, Inventory
from app.models.item import InventoryItem
from app.services.shop_service import (
    get_shop_items,
    purchase_item,
    get_user_inventory,
    toggle_inventory_item,
)

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/items")
async def list_items(
    item_type: ItemType | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_shop_items(db, item_type, sort_by, sort_dir, page)
    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "type": i.item_type,
                "price": str(i.price),
                "photo_url": i.photo_url,
                "stock": i.stock,
                "sold_count": i.sold_count,
                "initial_stock": (i.stock + i.sold_count) if i.stock is not None else None,
            }
            for i in items
        ],
        "total": total,
        "page": page,
    }


class PurchaseRequest(BaseModel):
    item_id: int


@router.post("/buy")
async def buy_item(
    body: PurchaseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        inv = await purchase_item(db, user, body.item_id)
        # Get the serial_uid for this purchase
        inst_result = await db.execute(
            select(InventoryItem).where(InventoryItem.inventory_id == inv.id)
        )
        instance = inst_result.scalar_one_or_none()
        return {
            "success": True,
            "inventory_id": inv.id,
            "serial_uid": instance.serial_uid if instance else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory")
async def my_inventory(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_user_inventory(db, user.tg_id)

    # Get serial_uids for each inventory item
    inv_ids = [inv.id for inv in items]
    serial_map: dict[int, str] = {}
    if inv_ids:
        inst_result = await db.execute(
            select(InventoryItem).where(InventoryItem.inventory_id.in_(inv_ids))
        )
        for inst in inst_result.scalars().all():
            if inst.inventory_id:
                serial_map[inst.inventory_id] = inst.serial_uid

    return {
        "inventory": [
            {
                "id": inv.id,
                "item_id": inv.item_id,
                "serial_uid": serial_map.get(inv.id),
                "is_active": inv.is_active,
                "bought_at": inv.bought_at.isoformat(),
                "item": {
                    "name": inv.item.name,
                    "type": inv.item.item_type,
                    "photo_url": inv.item.photo_url,
                } if inv.item else None,
            }
            for inv in items
        ]
    }


class ToggleRequest(BaseModel):
    inventory_id: int


@router.post("/inventory/toggle")
async def toggle_item(
    body: ToggleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        inv = await toggle_inventory_item(db, user.tg_id, body.inventory_id)
        return {"success": True, "is_active": inv.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
