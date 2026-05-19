"""Owner settings overview.

Shows all current BotSettings values.
Provides a button to reopen the Setup Wizard.
"""

import html as _html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters import IsOwner
from app.bot.keyboards.owner_inline import OwnerSettingCB, owner_settings_kb
from app.bot.keyboards.owner_reply import BTN_OWNER_SETTINGS
from app.bot.routers.owner.setup_wizard import (
    _validate_auction_timeout,
    _validate_max_orders,
    _validate_operator_payout,
    _validate_payment_requisites,
    _validate_service_name,
    _validate_support_contact,
    _validate_welcome_text,
)
from app.bot.states.owner_settings import OwnerSettingsEditStates
from app.services.settings_service import SettingsService

router = Router()


_CANCEL_HINT = "\n\nДля отмены — /cancel"

_SETTING_LABELS: dict[str, str] = {
    "service_name": "название сервиса",
    "welcome_text": "приветствие",
    "support_contact": "контакт поддержки",
    "payment_requisites": "реквизиты",
    "max_active_orders": "лимит заявок на клиента",
    "auction_timeout_minutes": "время аукциона",
    "operator_payout_percent": "% выплаты оператору",
}

_SETTING_PROMPTS: dict[str, str] = {
    "service_name": "Введите новое <b>название сервиса</b> (1–64 символа).",
    "welcome_text": "Введите новое <b>приветствие</b> для клиентов (1–500 символов).",
    "support_contact": "Введите новый <b>контакт поддержки</b>: @handle или «-», чтобы очистить.",
    "payment_requisites": "Введите новые <b>реквизиты</b> (до 1000 символов) или «-», чтобы очистить.",
    "max_active_orders": "Введите новый <b>лимит активных заявок</b> на клиента: число от 1 до 20.",
    "auction_timeout_minutes": "Введите новое <b>время аукциона</b> в минутах: число от 10 до 1440.",
    "operator_payout_percent": "Введите новый <b>% выплаты оператору</b>: число от 0 до 100.",
}


def _fmt(value: str, fallback: str = "не задано") -> str:
    return _html.escape(value) if value else fallback


def validate_setting_value(key: str, raw: str) -> tuple[bool, str, str]:
    """Validate one owner-editable setting and return (ok, value, error)."""
    if key == "service_name":
        value = _validate_service_name(raw)
        return (True, value, "") if value is not None else (False, "", "Название должно быть от 1 до 64 символов")
    if key == "welcome_text":
        value = _validate_welcome_text(raw)
        return (True, value, "") if value is not None else (False, "", "Приветствие должно быть от 1 до 500 символов")
    if key == "support_contact":
        ok, value = _validate_support_contact(raw)
        return (True, value, "") if ok else (False, "", "Введите @handle или «-», чтобы очистить")
    if key == "payment_requisites":
        value = _validate_payment_requisites(raw)
        return (True, value, "") if value is not None else (False, "", "Реквизиты должны быть не длиннее 1000 символов")
    if key == "max_active_orders":
        value = _validate_max_orders(raw)
        return (True, str(value), "") if value is not None else (False, "", "Введите целое число от 1 до 20")
    if key == "auction_timeout_minutes":
        value = _validate_auction_timeout(raw)
        return (True, str(value), "") if value is not None else (False, "", "Введите целое число от 10 до 1440")
    if key == "operator_payout_percent":
        value = _validate_operator_payout(raw)
        return (True, str(value), "") if value is not None else (False, "", "Введите целое число от 0 до 100")
    return False, "", "Неизвестная настройка"


async def _send_settings_card(message: Message, session: AsyncSession) -> None:
    svc = SettingsService(session=session)
    all_settings = await svc.get_all()

    support = _fmt(all_settings.get("support_contact", ""))
    requisites = _fmt(all_settings.get("payment_requisites", ""))

    text = (
        "⚙️ <b>Текущие настройки сервиса</b>\n\n"
        f"🏷 Название: <b>{_fmt(all_settings.get('service_name', ''))}</b>\n"
        f"👋 Приветствие:\n<i>{_fmt(all_settings.get('welcome_text', ''))}</i>\n\n"
        f"📞 Контакт поддержки: <b>{support}</b>\n"
        f"💳 Реквизиты: <b>{requisites}</b>\n\n"
        f"📦 Лимит заявок/клиент: <b>{_fmt(all_settings.get('max_active_orders', ''), '5')}</b>\n"
        f"⏱ Время аукциона: <b>{_fmt(all_settings.get('auction_timeout_minutes', ''), '120')} мин</b>\n"
        f"💰 % выплаты оператору: <b>{_fmt(all_settings.get('operator_payout_percent', ''), '70')}%</b>"
    )

    await message.answer(text, reply_markup=owner_settings_kb(), parse_mode="HTML")


@router.message(F.text == BTN_OWNER_SETTINGS, IsOwner())
async def owner_settings_view(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Show all current settings values to the owner."""
    await state.clear()
    await _send_settings_card(message, session)


@router.callback_query(OwnerSettingCB.filter(), IsOwner())
async def owner_setting_edit_start(
    callback: CallbackQuery,
    callback_data: OwnerSettingCB,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    key = callback_data.key
    prompt = _SETTING_PROMPTS.get(key)
    if prompt is None:
        await callback.answer("❌ Неизвестная настройка", show_alert=True)
        return

    current_value = await SettingsService(session=session).get(key)
    current_display = _html.escape(current_value) if current_value else "не задано"

    await state.set_state(OwnerSettingsEditStates.waiting_value)
    await state.update_data(setting_key=key)
    await callback.message.answer(
        f"✏️ Изменяем <b>{_SETTING_LABELS[key]}</b>\n"
        f"Текущее значение: <b>{current_display}</b>\n\n"
        f"{prompt}{_CANCEL_HINT}",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(OwnerSettingsEditStates.waiting_value, F.text, IsOwner())
async def owner_setting_edit_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    key = str(data.get("setting_key") or "")
    ok, value, error = validate_setting_value(key, message.text or "")
    if not ok:
        await message.answer(f"❌ {error}{_CANCEL_HINT}")
        return

    await SettingsService(session=session).set(key, value)
    await state.clear()
    await message.answer(f"✅ Настройка «{_SETTING_LABELS.get(key, key)}» сохранена")
    await _send_settings_card(message, session)


@router.message(OwnerSettingsEditStates.waiting_value, IsOwner())
async def owner_setting_edit_bad_type(message: Message) -> None:
    await message.answer(f"✏️ Введите новое значение текстом{_CANCEL_HINT}")
