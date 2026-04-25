from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import Item, Inventory, User, Transaction, TransactionType, TransactionStatus, ItemType, Room, InventoryItem
from decimal import Decimal


async def get_shop_items(
    db: AsyncSession,
    item_type: ItemType | None = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Item], int]:
    query = select(Item).where(Item.is_active == True)

    if item_type:
        query = query.where(Item.item_type == item_type)

    order_col = {
        "id": Item.id,
        "price_asc": Item.price,
        "price_desc": Item.price,
    }.get(sort_by, Item.id)

    if sort_by == "price_desc" or sort_dir == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    count_result = await db.execute(
        select(func.count()).select_from(Item).where(
            Item.is_active == True,
            *([Item.item_type == item_type] if item_type else [])
        )
    )
    total = count_result.scalar_one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_item_by_id(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def get_item_by_serial_uid(db: AsyncSession, serial_uid: str) -> InventoryItem | None:
    """Найти экземпляр предмета по его serial_uid (например '1.001')"""
    result = await db.execute(
        select(InventoryItem)
        .options(selectinload(InventoryItem.item))
        .where(InventoryItem.serial_uid == serial_uid)
    )
    return result.scalar_one_or_none()


async def purchase_item(db: AsyncSession, user: User, item_id: int) -> Inventory:
    result = await db.execute(select(Item).where(Item.id == item_id, Item.is_active == True))
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError("Товар не найден или недоступен")

    if item.stock is not None and item.stock <= 0:
        raise ValueError("Товар закончился")

    if user.balance < item.price:
        raise ValueError("Недостаточно средств")

    user.balance -= item.price
    item.sold_count += 1
    if item.stock is not None:
        item.stock -= 1
        if item.stock == 0:
            item.is_active = False
    await db.flush()

    inv = Inventory(user_id=user.tg_id, item_id=item.id, is_active=False)
    db.add(inv)
    await db.flush()

    # Привязываем свободный экземпляр (InventoryItem) к этой покупке
    inst_result = await db.execute(
        select(InventoryItem)
        .where(InventoryItem.item_id == item.id, InventoryItem.inventory_id == None)
        .order_by(InventoryItem.serial_number)
        .limit(1)
    )
    instance = inst_result.scalar_one_or_none()
    if instance:
        instance.inventory_id = inv.id
        await db.flush()

    tx = Transaction(
        user_id=user.tg_id,
        tx_type=TransactionType.purchase,
        amount=item.price,
        status=TransactionStatus.completed,
        note=f"Покупка: {item.name} (id={item.id}) serial={instance.serial_uid if instance else '—'}",
    )
    db.add(tx)
    await db.flush()

    return inv


async def toggle_inventory_item(
    db: AsyncSession,
    user_id: int,
    inventory_id: int,
) -> Inventory:
    result = await db.execute(
        select(Inventory).where(
            Inventory.id == inventory_id,
            Inventory.user_id == user_id,
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise ValueError("Предмет не найден в инвентаре")

    inv.is_active = not inv.is_active
    await db.flush()
    return inv


async def get_user_inventory(
    db: AsyncSession,
    user_id: int,
    only_active: bool = False,
) -> list[Inventory]:
    query = select(Inventory).options(selectinload(Inventory.item)).where(Inventory.user_id == user_id)
    if only_active:
        query = query.where(Inventory.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


async def create_item(
    db: AsyncSession,
    name: str,
    description: str | None,
    item_type: ItemType,
    price: Decimal,
    photo_url: str | None,
    stock: int | None,
) -> Item:
    item = Item(
        name=name,
        description=description,
        item_type=item_type,
        price=price,
        photo_url=photo_url,
        stock=stock,
    )
    db.add(item)
    await db.flush()  # получаем item.id

    # Генерируем экземпляры InventoryItem с serial_uid = "{item.id}.{N:03d}"
    if stock is not None and stock > 0:
        # Определяем ширину номера: если stock > 999, используем 4 знака, иначе 3
        width = max(3, len(str(stock)))
        for n in range(1, stock + 1):
            serial_uid = f"{item.id}.{str(n).zfill(width)}"
            inst = InventoryItem(
                item_id=item.id,
                serial_uid=serial_uid,
                serial_number=n,
            )
            db.add(inst)
        await db.flush()

    return item


async def find_item_owner(db: AsyncSession, item_id: int) -> list[Inventory]:
    """Найти все записи инвентаря для предмета по его ID"""
    result = await db.execute(
        select(Inventory)
        .options(selectinload(Inventory.user), selectinload(Inventory.item))
        .where(Inventory.item_id == item_id)
    )
    return result.scalars().all()


async def find_item_instances(db: AsyncSession, item_id: int) -> list[InventoryItem]:
    """Все экземпляры предмета (serial_uid список)"""
    result = await db.execute(
        select(InventoryItem)
        .where(InventoryItem.item_id == item_id)
        .order_by(InventoryItem.serial_number)
    )
    return result.scalars().all()