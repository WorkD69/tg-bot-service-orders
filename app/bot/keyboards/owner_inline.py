from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class WizardCB(CallbackData, prefix="wizard"):
    """Callback for wizard confirm screen buttons."""
    action: str  # save | restart


class OwnerSettingCB(CallbackData, prefix="owner_setting"):
    """Callback for editing one owner setting."""

    key: str


def wizard_confirm_kb() -> InlineKeyboardMarkup:
    """Inline keyboard shown at the wizard confirm step."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Сохранить",
                    callback_data=WizardCB(action="save").pack(),
                ),
                InlineKeyboardButton(
                    text="🔄 Начать заново",
                    callback_data=WizardCB(action="restart").pack(),
                ),
            ]
        ]
    )


def owner_settings_kb() -> InlineKeyboardMarkup:
    """Inline keyboard on the settings overview screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏷 Изменить название",
                    callback_data=OwnerSettingCB(key="service_name").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👋 Изменить приветствие",
                    callback_data=OwnerSettingCB(key="welcome_text").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📞 Изменить контакт",
                    callback_data=OwnerSettingCB(key="support_contact").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💳 Изменить реквизиты",
                    callback_data=OwnerSettingCB(key="payment_requisites").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Изменить лимит заявок",
                    callback_data=OwnerSettingCB(key="max_active_orders").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏱ Изменить время аукциона",
                    callback_data=OwnerSettingCB(key="auction_timeout_minutes").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰 Изменить % выплаты",
                    callback_data=OwnerSettingCB(key="operator_payout_percent").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🧙 Изменить все настройки",
                    callback_data=WizardCB(action="restart").pack(),
                )
            ]
        ]
    )
