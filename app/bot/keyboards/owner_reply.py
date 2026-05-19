from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_OWNER_SETTINGS = "⚙️ Настройки"
BTN_OWNER_WIZARD = "🧙 Мастер настройки"


def owner_main_kb() -> ReplyKeyboardMarkup:
    """Main reply keyboard for the owner role."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_OWNER_SETTINGS)],
            [KeyboardButton(text=BTN_OWNER_WIZARD)],
        ],
        resize_keyboard=True,
    )
