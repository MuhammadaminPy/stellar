from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from decimal import Decimal
from app.core.config import settings
from app.models import User, Transaction, TransactionType, TransactionStatus, ItemType
from app.services.shop_service import create_item, find_item_owner, get_item_by_id, get_item_by_serial_uid
from app.bot.keyboards import admin_menu_kb, item_types_kb, withdrawal_kb

router = Router()


def is_admin(tg_id: int) -> bool:
    return tg_id in settings.admin_ids_list


class AdminStates(StatesGroup):
    broadcast_text = State()
    user_id = State()
    adjust_balance_amount = State()
    add_item_type = State()
    add_item_name = State()
    add_item_desc = State()
    add_item_photo = State()
    add_item_price = State()
    add_item_stock = State()
    find_item_id = State()
    ref_percent_user = State()
    ref_percent_value = State()
    bonus_value = State()
    pet_feed_interval = State()
    pet_pet_interval = State()
    pet_feed_price = State()
    pet_bulk_price = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Админ-панель:", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:stats")
async def cb_stats(call: CallbackQuery, db: AsyncSession):
    if not is_admin(call.from_user.id):
        return
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    new_users = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= day_ago)
    )).scalar_one()
    deposited = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.tx_type == TransactionType.deposit, Transaction.status == TransactionStatus.completed)
    )).scalar_one()
    withdrawn = (await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.tx_type == TransactionType.withdraw, Transaction.status == TransactionStatus.completed)
    )).scalar_one()

    await call.message.edit_text(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"🆕 Новых за 24ч: <b>{new_users}</b>\n"
        f"💰 Всего пополнено: <b>{deposited} $DF</b>\n"
        f"💸 Всего выведено: <b>{withdrawn} $DF</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("📢 Введите текст рассылки (поддерживается HTML):")
    await state.set_state(AdminStates.broadcast_text)
    await call.answer()


@router.message(AdminStates.broadcast_text)
async def do_broadcast(message: Message, state: FSMContext, db: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    text = message.text
    result = await db.execute(select(User.tg_id))
    user_ids = result.scalars().all()

    bot = message.bot
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {failed}")
    await state.clear()


@router.callback_query(F.data == "admin:user")
async def cb_user_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("👤 Введите Telegram ID игрока:")
    await state.set_state(AdminStates.user_id)
    await call.answer()


@router.message(AdminStates.user_id)
async def get_user_info(message: Message, state: FSMContext, db: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        tg_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        await state.clear()
        return

    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        await message.answer("❌ Пользователь не найден")
        await state.clear()
        return

    await state.update_data(target_user_id=tg_id)
    await message.answer(
        f"👤 <b>{user.full_name}</b> (@{user.username})\n"
        f"ID: <code>{user.tg_id}</code>\n"
        f"Баланс: <b>{user.balance} $DF</b>\n"
        f"Реф-код: <code>{user.ref_code}</code>\n"
        f"Реф %: <b>{user.ref_percent}%</b>\n\n"
        f"Введите сумму для корректировки баланса (+ или -):",
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.adjust_balance_amount)


@router.message(AdminStates.adjust_balance_amount)
async def do_adjust_balance(message: Message, state: FSMContext, db: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    tg_id = data["target_user_id"]
    try:
        amount = Decimal(message.text.strip())
    except Exception:
        await message.answer("❌ Неверная сумма")
        await state.clear()
        return

    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one()
    user.balance += amount
    tx_type = TransactionType.admin_add if amount >= 0 else TransactionType.admin_sub
    db.add(Transaction(
        user_id=tg_id,
        tx_type=tx_type,
        amount=abs(amount),
        status=TransactionStatus.completed,
        note=f"Корректировка админом {message.from_user.id}",
    ))
    await db.flush()

    await message.answer(f"✅ Баланс обновлён: <b>{user.balance} $DF</b>", parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "admin:add_item")
async def cb_add_item(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("Выберите тип товара:", reply_markup=item_types_kb("add_item"))
    await state.set_state(AdminStates.add_item_type)
    await call.answer()


@router.callback_query(F.data.startswith("add_item:"))
async def cb_add_item_type(call: CallbackQuery, state: FSMContext):
    item_type = call.data.split(":")[1]
    await state.update_data(item_type=item_type)
    await call.message.answer("Введите название товара:")
    await state.set_state(AdminStates.add_item_name)
    await call.answer()


@router.message(AdminStates.add_item_name)
async def add_item_name(message: Message, state: FSMContext):
    await state.update_data(item_name=message.text)
    await message.answer("Введите описание товара (или '-' чтобы пропустить):")
    await state.set_state(AdminStates.add_item_desc)


@router.message(AdminStates.add_item_desc)
async def add_item_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else None
    await state.update_data(item_desc=desc)
    await message.answer("Отправьте фото товара (или '-' чтобы пропустить):")
    await state.set_state(AdminStates.add_item_photo)


@router.message(AdminStates.add_item_photo)
async def add_item_photo(message: Message, state: FSMContext):
    photo_url = None
    if message.photo:
        file_id = message.photo[-1].file_id
        try:
            file = await message.bot.get_file(file_id)
            token = message.bot.token
            photo_url = f"https://api.telegram.org/file/bot{token}/{file.file_path}"
        except Exception:
            photo_url = None
    await state.update_data(item_photo=photo_url)
    await message.answer("Введите цену в $DF:")
    await state.set_state(AdminStates.add_item_price)


@router.message(AdminStates.add_item_price)
async def add_item_price(message: Message, state: FSMContext):
    await state.update_data(item_price=message.text)
    await message.answer("Введите количество товара (или '-' для безлимитного):")
    await state.set_state(AdminStates.add_item_stock)


@router.message(AdminStates.add_item_stock)
async def add_item_stock(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    stock = int(message.text) if message.text.isdigit() else None

    item = await create_item(
        db,
        name=data["item_name"],
        description=data.get("item_desc"),
        item_type=ItemType(data["item_type"]),
        price=Decimal(data["item_price"]),
        photo_url=data.get("item_photo"),
        stock=stock,
    )
    await message.answer(f"✅ Товар добавлен! ID: <b>{item.id}</b>", parse_mode="HTML")
    await state.clear()


# ─────────────────── НАЙТИ ТОВАР ПО ID ───────────────────

@router.callback_query(F.data == "admin:find_item")
async def cb_find_item(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("🔍 Введите ID товара (число) или serial_uid (например 1.001):")
    await state.set_state(AdminStates.find_item_id)
    await call.answer()


@router.message(AdminStates.find_item_id)
async def do_find_item(message: Message, state: FSMContext, db: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()
    await state.clear()

    # If contains dot — it's a serial_uid
    if "." in query:
        instance = await get_item_by_serial_uid(db, query)
        if not instance:
            await message.answer(f"❌ Экземпляр '{query}' не найден")
            return

        from app.models import Inventory
        owner_text = "Не продан"
        if instance.inventory_id:
            inv_result = await db.execute(select(Inventory).where(Inventory.id == instance.inventory_id))
            inv = inv_result.scalar_one_or_none()
            if inv:
                owner_text = f"Владелец: <code>{inv.user_id}</code> (куплен {inv.bought_at.strftime('%d.%m.%Y')})"

        await message.answer(
            f"🔍 <b>Экземпляр {instance.serial_uid}</b>\n"
            f"Товар: {instance.item.name} (ID: {instance.item_id})\n"
            f"Серийный №: {instance.serial_number}\n"
            f"{owner_text}",
            parse_mode="HTML",
        )
    else:
        # Search by item ID
        try:
            item_id = int(query)
        except ValueError:
            await message.answer("❌ Введите число (ID товара) или serial_uid (например 1.001)")
            return

        item = await get_item_by_id(db, item_id)
        if not item:
            await message.answer(f"❌ Товар с ID {item_id} не найден")
            return

        owners = await find_item_owner(db, item_id)
        await message.answer(
            f"🛒 <b>{item.name}</b> (ID: {item.id})\n"
            f"Тип: {item.item_type.value}\n"
            f"Цена: {item.price} $DF\n"
            f"Остаток: {item.stock if item.stock is not None else '∞'}\n"
            f"Продано: {item.sold_count}\n"
            f"Активен: {'✅' if item.is_active else '❌'}\n"
            f"Покупателей: {len(owners)}",
            parse_mode="HTML",
        )


# ─────────────────── ЗАЯВКИ НА ВЫВОД ───────────────────

@router.callback_query(F.data == "admin:withdrawals")
async def cb_withdrawals(call: CallbackQuery, db: AsyncSession):
    if not is_admin(call.from_user.id):
        return
    result = await db.execute(
        select(Transaction).where(
            Transaction.tx_type == TransactionType.withdraw,
            Transaction.status == TransactionStatus.pending,
        ).limit(10)
    )
    txs = result.scalars().all()
    if not txs:
        await call.message.answer("✅ Нет ожидающих заявок на вывод")
        await call.answer()
        return

    for tx in txs:
        await call.message.answer(
            f"💸 Заявка #{tx.id}\n"
            f"Игрок: <code>{tx.user_id}</code>\n"
            f"Сумма: <b>{tx.amount} $DF</b>\n"
            f"Кошелёк: <code>{tx.wallet_address}</code>",
            reply_markup=withdrawal_kb(tx.id),
            parse_mode="HTML",
        )
    await call.answer()


@router.callback_query(F.data.startswith("withdraw:"))
async def cb_withdrawal_action(call: CallbackQuery, db: AsyncSession):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    action = parts[1]
    tx_id = int(parts[2])

    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        await call.answer("Транзакция не найдена")
        return

    if action == "approve":
        tx.status = TransactionStatus.completed
        user_result = await db.execute(select(User).where(User.tg_id == tx.user_id))
        user = user_result.scalar_one()
        user.total_withdrawn += tx.amount
        status_text = "✅ Одобрено"
    else:
        tx.status = TransactionStatus.rejected
        user_result = await db.execute(select(User).where(User.tg_id == tx.user_id))
        user = user_result.scalar_one()
        user.balance += tx.amount
        status_text = "❌ Отклонено"

    await db.flush()
    await call.message.edit_text(
        call.message.text + f"\n\n<b>{status_text}</b>",
        parse_mode="HTML",
    )

    try:
        notify_text = (
            f"✅ Ваш вывод на {tx.amount} $DF одобрен и отправлен!"
            if action == "approve"
            else f"❌ Ваш запрос на вывод {tx.amount} $DF отклонён. Средства возвращены."
        )
        await call.bot.send_message(tx.user_id, notify_text)
    except Exception:
        pass

    await call.answer(status_text)


# ─────────────────── БОНУС ───────────────────

@router.callback_query(F.data == "admin:bonus")
async def cb_bonus(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("🎁 Введите % бонуса при пополнении (0 = отключить):")
    await state.set_state(AdminStates.bonus_value)
    await call.answer()


@router.message(AdminStates.bonus_value)
async def do_set_bonus(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        percent = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число")
        await state.clear()
        return
    from app.core import config as cfg
    cfg.settings.DEPOSIT_BONUS_PERCENT = percent
    await message.answer(f"✅ Бонус установлен: <b>{percent}%</b>", parse_mode="HTML")
    await state.clear()


# ─────────────────── ТОП РЕФОВОДОВ (ИСПРАВЛЕН) ───────────────────

@router.callback_query(F.data == "admin:top_refs")
async def cb_top_refs(call: CallbackQuery, db: AsyncSession):
    if not is_admin(call.from_user.id):
        return

    Referral = aliased(User, name="referral")
    result = await db.execute(
        select(
            User.tg_id,
            User.full_name,
            User.username,
            User.ref_code,
            func.count(Referral.tg_id).label("ref_count"),
        )
        .outerjoin(Referral, Referral.referrer_id == User.tg_id)
        .group_by(User.tg_id, User.full_name, User.username, User.ref_code)
        .order_by(func.count(Referral.tg_id).desc())
        .limit(10)
    )
    rows = result.all()

    lines = ["🏆 <b>Топ рефоводов</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    rank = 0
    for row in rows:
        if row.ref_count == 0:
            continue
        rank += 1
        medal = medals[rank - 1] if rank <= 3 else f"{rank}."
        name = row.full_name or row.username or f"#{row.tg_id}"
        lines.append(f"{medal} {name} — <b>{row.ref_count} реф.</b>")
        if rank >= 10:
            break

    if rank == 0:
        lines.append("Пока нет рефоводов")

    await call.message.answer("\n".join(lines), parse_mode="HTML")
    await call.answer()


# ─────────────────── РЕФ % ИГРОКА ───────────────────

@router.callback_query(F.data == "admin:ref_percent")
async def cb_ref_percent(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("Введите ID игрока для изменения реф %:")
    await state.set_state(AdminStates.ref_percent_user)
    await call.answer()


@router.message(AdminStates.ref_percent_user)
async def ref_percent_user(message: Message, state: FSMContext):
    await state.update_data(ref_user_id=int(message.text.strip()))
    await message.answer("Введите новый % отчислений от рефералов:")
    await state.set_state(AdminStates.ref_percent_value)


@router.message(AdminStates.ref_percent_value)
async def ref_percent_value(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    tg_id = data["ref_user_id"]
    try:
        percent = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число")
        await state.clear()
        return

    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        await message.answer("❌ Пользователь не найден")
    else:
        user.ref_percent = percent
        await db.flush()
        await message.answer(f"✅ Реф % для {tg_id} установлен: <b>{percent}%</b>", parse_mode="HTML")
    await state.clear()


# ─────────────────── НАСТРОЙКИ ПИТОМЦА ───────────────────

@router.callback_query(F.data == "admin:pet_settings")
async def cb_pet_settings(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    s = settings
    await call.message.answer(
        f"🐾 <b>Настройки питомца</b>\n\n"
        f"Интервал корма: {s.PET_FEED_INTERVAL_HOURS} ч.\n"
        f"Интервал поглаживания: {s.PET_PET_INTERVAL_HOURS} ч.\n"
        f"Цена корма: {s.PET_FEED_PRICE} $DF\n"
        f"Цена bulk корма ({s.PET_FEED_BULK_HOURS} ч.): {s.PET_FEED_BULK_PRICE} $DF\n"
        f"Лимит пропусков до смерти: {s.PET_MISS_LIMIT}\n\n"
        f"Введите новый интервал корма (часы) или 0 чтобы пропустить:",
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.pet_feed_interval)
    await call.answer()


@router.message(AdminStates.pet_feed_interval)
async def pet_feed_interval(message: Message, state: FSMContext):
    val = message.text.strip()
    if val.isdigit() and int(val) > 0:
        settings.PET_FEED_INTERVAL_HOURS = int(val)
    await message.answer(f"Введите интервал поглаживания (часы):")
    await state.set_state(AdminStates.pet_pet_interval)


@router.message(AdminStates.pet_pet_interval)
async def pet_pet_interval(message: Message, state: FSMContext):
    val = message.text.strip()
    if val.isdigit() and int(val) > 0:
        settings.PET_PET_INTERVAL_HOURS = int(val)
    await message.answer(f"Введите цену разового корма ($DF):")
    await state.set_state(AdminStates.pet_feed_price)


@router.message(AdminStates.pet_feed_price)
async def pet_feed_price_handler(message: Message, state: FSMContext):
    val = message.text.strip()
    try:
        settings.PET_FEED_PRICE = float(val)
    except ValueError:
        pass
    await message.answer(f"Введите цену bulk корма на {settings.PET_FEED_BULK_HOURS} ч. ($DF):")
    await state.set_state(AdminStates.pet_bulk_price)


@router.message(AdminStates.pet_bulk_price)
async def pet_bulk_price_handler(message: Message, state: FSMContext):
    val = message.text.strip()
    try:
        settings.PET_FEED_BULK_PRICE = float(val)
    except ValueError:
        pass

    s = settings
    await message.answer(
        f"✅ <b>Настройки питомца обновлены!</b>\n\n"
        f"Интервал корма: {s.PET_FEED_INTERVAL_HOURS} ч.\n"
        f"Интервал поглаживания: {s.PET_PET_INTERVAL_HOURS} ч.\n"
        f"Цена корма: {s.PET_FEED_PRICE} $DF\n"
        f"Цена bulk ({s.PET_FEED_BULK_HOURS} ч.): {s.PET_FEED_BULK_PRICE} $DF",
        parse_mode="HTML",
    )
    await state.clear()
