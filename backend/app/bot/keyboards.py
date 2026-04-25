from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,  # ИСПРАВЛЕНО: необходимый импорт для web_app кнопки
)
from app.core.config import settings


def main_menu_kb() -> InlineKeyboardMarkup:
    webapp_url = settings.WEBAPP_URL.strip()
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🏠 Открыть приложение",
                web_app=WebAppInfo(url=webapp_url),
            )
        ]]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast"),
        ],
        [
            InlineKeyboardButton(text="👤 Игрок", callback_data="admin:user"),
            InlineKeyboardButton(text="💸 Выводы", callback_data="admin:withdrawals"),
        ],
        [
            InlineKeyboardButton(text="🛒 Добавить товар", callback_data="admin:add_item"),
            InlineKeyboardButton(text="🔍 Найти товар", callback_data="admin:find_item"),
        ],
        [
            InlineKeyboardButton(text="🏆 Топ рефоводов", callback_data="admin:top_refs"),
            InlineKeyboardButton(text="🎁 Бонус пополнения", callback_data="admin:bonus"),
        ],
        [
            InlineKeyboardButton(text="👥 Реф %", callback_data="admin:ref_percent"),
            InlineKeyboardButton(text="🐾 Питомцы", callback_data="admin:pet_settings"),
        ],
    ])


def item_types_kb(prefix: str) -> InlineKeyboardMarkup:
    from app.models.item import ItemType
    buttons = [
        InlineKeyboardButton(text=t.value.capitalize(), callback_data=f"{prefix}:{t.value}")
        for t in ItemType
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def withdrawal_kb(tx_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"withdraw:approve:{tx_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"withdraw:reject:{tx_id}"),
    ]])
