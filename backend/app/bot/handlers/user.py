from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.user_service import get_or_create_user, get_user_by_ref_code, activate_user_by_ref_code
from app.services.pet_service import create_pet
from app.models import User
from app.bot.keyboards import main_menu_kb
from app.core.config import settings

router = Router()


class UserStates(StatesGroup):
    choosing_pet = State()


def choose_pet_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🐱 Кошка", callback_data="choose_pet:cat"),
            InlineKeyboardButton(text="🐶 Собака", callback_data="choose_pet:dog"),
        ]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession, state: FSMContext):
    user, is_new = await get_or_create_user(
        db,
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referrer_tg_id=None,
    )

    if not user.has_chosen_pet:
        await state.set_state(UserStates.choosing_pet)
        await message.answer(
            f"🐾 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
            f"Выбери своего первого питомца — он будет жить в твоей квартире!\n"
            f"За ним нужно ухаживать: кормить и гладить 🤝",
            parse_mode="HTML",
            reply_markup=choose_pet_kb(),
        )
        return

    if is_new:
        text = (
            f"👋 Добро пожаловать, <b>{message.from_user.first_name}</b>!\n\n"
            f"🏠 Здесь ты можешь украшать свой дом, торговать токенами <b>$DF</b> "
            f"и соревноваться с соседями.\n\n"
            f"💡 В мини-приложении можно ввести реф код друга, чтобы связаться с ним.\n\n"
            f"Нажми кнопку ниже чтобы открыть приложение:"
        )
    else:
        text = (
            f"👋 С возвращением, <b>{message.from_user.first_name}</b>!\n\n"
            f"Открывай приложение и продолжай:"
        )

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("choose_pet:"))
async def cb_choose_pet(call: CallbackQuery, state: FSMContext, db: AsyncSession):
    pet_type = call.data.split(":")[1]
    if pet_type not in ("cat", "dog"):
        await call.answer("Неверный выбор")
        return

    result = await db.execute(select(User).where(User.tg_id == call.from_user.id))
    user = result.scalar_one_or_none()
    if not user:
        await call.answer("Ошибка")
        return

    if user.has_chosen_pet:
        await call.answer("Питомец уже выбран!")
        await call.message.answer(
            "🏠 Открывай приложение:",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    await create_pet(db, user.tg_id, pet_type)
    user.has_chosen_pet = True
    await db.flush()

    emoji = "🐱" if pet_type == "cat" else "🐶"
    name = "Кошка" if pet_type == "cat" else "Собака"

    # ИСПРАВЛЕНО: call.bot заменён на settings.PET_FEED_INTERVAL_HOURS
    await call.message.edit_text(
        f"{emoji} Отлично! Твой питомец <b>{name}</b> уже живёт в твоей квартире!\n\n"
        f"🍖 Корми раз в {settings.PET_FEED_INTERVAL_HOURS}ч (стоит токены)\n"
        f"🤝 Гладь раз в {settings.PET_PET_INTERVAL_HOURS}ч (бесплатно)\n\n"
        f"Если забудешь {settings.PET_MISS_LIMIT} раза — питомец погибнет 😢",
        parse_mode="HTML",
    )

    await call.message.answer(
        "🏠 Открывай приложение и начинай играть!",
        reply_markup=main_menu_kb(),
    )
    await state.clear()
    await call.answer()
