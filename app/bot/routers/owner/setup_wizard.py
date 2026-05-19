"""Owner Setup Wizard - 7-step FSM for business configuration.

Flow:
    /start (owner) or BTN_OWNER_WIZARD
        -> step 1: service_name
        -> step 2: welcome_text
        -> step 3: support_contact
        -> step 4: payment_requisites
        -> step 5: max_active_orders
        -> step 6: auction_timeout_minutes
        -> step 7: operator_payout_percent
        -> confirm: summary + [Save] [Restart]
        -> saved to bot_settings via SettingsService
"""

import html
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters import IsOwner
from app.bot.keyboards.owner_inline import WizardCB, wizard_confirm_kb
from app.bot.keyboards.owner_reply import BTN_OWNER_WIZARD, owner_main_kb
from app.bot.states.setup_wizard import SetupWizardStates
from app.services.settings_service import SettingsService

router = Router()

_CANCEL_HINT = "\n\nДля отмены — /cancel"

# Telegram username: @, then a letter, then 4-31 word chars (total 5-32 after @)
_HANDLE_RE = re.compile(r"^@[A-Za-z]\w{4,31}$")


def _with_cancel(text: str) -> str:
    return f"{text}{_CANCEL_HINT}"


def _validate_service_name(raw: str) -> str | None:
    v = raw.strip()
    return v if 1 <= len(v) <= 64 else None


def _validate_welcome_text(raw: str) -> str | None:
    v = raw.strip()
    return v if 1 <= len(v) <= 500 else None


def _validate_support_contact(raw: str) -> tuple[bool, str]:
    """Return (ok, cleaned_value).

    Accepts: @handle, "-" or empty (stored as "")
    Rejects: anything else.
    """
    v = raw.strip()
    if v in ("-", ""):
        return True, ""
    if _HANDLE_RE.match(v):
        return True, v
    return False, ""


def _validate_payment_requisites(raw: str) -> str | None:
    v = raw.strip()
    if v == "-":
        return ""
    return v if len(v) <= 1000 else None


def _validate_max_orders(raw: str) -> int | None:
    try:
        n = int(raw.strip())
        return n if 1 <= n <= 20 else None
    except ValueError:
        return None


def _validate_auction_timeout(raw: str) -> int | None:
    try:
        n = int(raw.strip())
        return n if 10 <= n <= 1440 else None
    except ValueError:
        return None


def _validate_operator_payout(raw: str) -> int | None:
    try:
        n = int(raw.strip())
        return n if 0 <= n <= 100 else None
    except ValueError:
        return None


async def start_wizard(message: Message, state: FSMContext) -> None:
    """Start (or restart) the setup wizard from step 1."""
    await state.set_state(SetupWizardStates.waiting_service_name)
    await state.update_data(
        service_name=None,
        welcome_text=None,
        support_contact=None,
        payment_requisites=None,
        max_active_orders=None,
        auction_timeout_minutes=None,
        operator_payout_percent=None,
    )
    await message.answer(
        _with_cancel(
            "🧙 Мастер настройки — Шаг 1 из 7\n\n"
            "Введите <b>название вашего сервиса</b> (1–64 символа).\n"
            "Например: «Ремонт техники» или «Студия дизайна»"
        ),
        parse_mode="HTML",
    )


@router.message(F.text == BTN_OWNER_WIZARD, IsOwner())
async def btn_wizard(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is not None:
        await state.clear()
    await start_wizard(message, state)


@router.message(SetupWizardStates.waiting_service_name, F.text, IsOwner())
async def wizard_service_name(message: Message, state: FSMContext) -> None:
    value = _validate_service_name(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Название должно быть от 1 до 64 символов\n"
            "Введите корректное название сервиса"
        ))
        return
    await state.update_data(service_name=value)
    await state.set_state(SetupWizardStates.waiting_welcome_text)
    await message.answer(
        _with_cancel(
            f"✅ Название: <b>{html.escape(value)}</b>\n\n"
            "🧙 Шаг 2 из 7\n\n"
            "Введите <b>приветствие для клиентов</b> (1–500 символов).\n"
            "Это текст, который клиент увидит при первом /start.\n"
            "Например: «Добро пожаловать! Оставьте заявку и мы с вами свяжемся»"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_service_name, IsOwner())
async def wizard_service_name_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите название сервиса текстом"))


@router.message(SetupWizardStates.waiting_welcome_text, F.text, IsOwner())
async def wizard_welcome_text(message: Message, state: FSMContext) -> None:
    value = _validate_welcome_text(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Приветствие должно быть от 1 до 500 символов\n"
            "Сократите текст или введите заново"
        ))
        return
    await state.update_data(welcome_text=value)
    await state.set_state(SetupWizardStates.waiting_support_contact)
    await message.answer(
        _with_cancel(
            "✅ Приветствие сохранено\n\n"
            "🧙 Шаг 3 из 7\n\n"
            "Введите <b>контакт поддержки</b> — @handle вашей поддержки.\n"
            "Клиенты увидят его в сообщениях об оплате и спорах.\n"
            "Если контакта нет — отправьте «-»"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_welcome_text, IsOwner())
async def wizard_welcome_text_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите приветствие текстом"))


@router.message(SetupWizardStates.waiting_support_contact, F.text, IsOwner())
async def wizard_support_contact(message: Message, state: FSMContext) -> None:
    ok, value = _validate_support_contact(message.text)
    if not ok:
        await message.answer(_with_cancel(
            "❌ Неверный формат\n"
            "Введите @handle (например @myshop_support) или «-» чтобы пропустить"
        ))
        return
    await state.update_data(support_contact=value)
    await state.set_state(SetupWizardStates.waiting_payment_requisites)
    display = value if value else "не указан"
    await message.answer(
        _with_cancel(
            f"✅ Контакт поддержки: <b>{display}</b>\n\n"
            "🧙 Шаг 4 из 7\n\n"
            "Введите <b>реквизиты для оплаты</b> (до 1000 символов).\n"
            "Это текст, который оператор отправит клиенту при оплате.\n"
            "Например: «Сбербанк: 4276 1234 5678 9012 Иван И.»\n"
            "Если реквизитов нет — отправьте «-»"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_support_contact, IsOwner())
async def wizard_support_contact_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите @handle поддержки или «-»"))


@router.message(SetupWizardStates.waiting_payment_requisites, F.text, IsOwner())
async def wizard_payment_requisites(message: Message, state: FSMContext) -> None:
    value = _validate_payment_requisites(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Слишком длинный текст (максимум 1000 символов)\n"
            "Сократите реквизиты или отправьте «-»"
        ))
        return
    await state.update_data(payment_requisites=value)
    await state.set_state(SetupWizardStates.waiting_max_orders)
    display = html.escape(value) if value else "не указаны"
    await message.answer(
        _with_cancel(
            f"✅ Реквизиты: <b>{display}</b>\n\n"
            "🧙 Шаг 5 из 7\n\n"
            "Введите <b>максимальное количество активных заявок</b> на одного клиента.\n"
            "Целое число от 1 до 20.\n"
            "Рекомендация: 5"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_payment_requisites, IsOwner())
async def wizard_payment_requisites_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите реквизиты текстом или «-»"))


@router.message(SetupWizardStates.waiting_max_orders, F.text, IsOwner())
async def wizard_max_orders(message: Message, state: FSMContext) -> None:
    value = _validate_max_orders(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Введите целое число от 1 до 20\n"
            "Например: 5"
        ))
        return
    await state.update_data(max_active_orders=value)
    await state.set_state(SetupWizardStates.waiting_auction_timeout)
    await message.answer(
        _with_cancel(
            f"✅ Лимит заявок: <b>{value}</b>\n\n"
            "🧙 Шаг 6 из 7\n\n"
            "Введите <b>время сбора ставок</b> в минутах (10–1440).\n"
            "Столько времени операторы смогут делать ставки после создания заявки.\n"
            "Рекомендация: 120 (2 часа)"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_max_orders, IsOwner())
async def wizard_max_orders_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите число от 1 до 20"))


@router.message(SetupWizardStates.waiting_auction_timeout, F.text, IsOwner())
async def wizard_auction_timeout(message: Message, state: FSMContext) -> None:
    value = _validate_auction_timeout(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Введите целое число от 10 до 1440 минут\n"
            "Например: 120"
        ))
        return
    await state.update_data(auction_timeout_minutes=value)
    await state.set_state(SetupWizardStates.waiting_operator_payout)
    await message.answer(
        _with_cancel(
            f"✅ Время аукциона: <b>{value} мин</b>\n\n"
            "🧙 Шаг 7 из 7\n\n"
            "Введите <b>процент выплаты оператору</b> от суммы заказа.\n"
            "Целое число от 0 до 100.\n"
            "Рекомендация: 70"
        ),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_auction_timeout, IsOwner())
async def wizard_auction_timeout_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите число минут от 10 до 1440"))


@router.message(SetupWizardStates.waiting_operator_payout, F.text, IsOwner())
async def wizard_operator_payout(message: Message, state: FSMContext) -> None:
    value = _validate_operator_payout(message.text)
    if value is None:
        await message.answer(_with_cancel(
            "❌ Введите целое число от 0 до 100\n"
            "Например: 70"
        ))
        return
    await state.update_data(operator_payout_percent=value)
    await state.set_state(SetupWizardStates.confirming)

    data = await state.get_data()
    await message.answer(
        _build_summary(data),
        reply_markup=wizard_confirm_kb(),
        parse_mode="HTML",
    )


@router.message(SetupWizardStates.waiting_operator_payout, IsOwner())
async def wizard_operator_payout_bad_type(message: Message) -> None:
    await message.answer(_with_cancel("✏️ Введите процент выплаты числом от 0 до 100"))


def _build_summary(data: dict) -> str:
    support = html.escape(data.get("support_contact") or "не указан")
    requisites = html.escape(data.get("payment_requisites") or "не указаны")
    svc_name = html.escape(str(data.get("service_name", "—")))
    welcome = html.escape(str(data.get("welcome_text", "—")))
    return (
        "📋 <b>Проверьте настройки перед сохранением:</b>\n\n"
        f"1️⃣ Название сервиса: <b>{svc_name}</b>\n"
        f"2️⃣ Приветствие: <i>{welcome}</i>\n"
        f"3️⃣ Контакт поддержки: <b>{support}</b>\n"
        f"4️⃣ Реквизиты: <b>{requisites}</b>\n"
        f"5️⃣ Лимит заявок/клиент: <b>{data.get('max_active_orders', '—')}</b>\n"
        f"6️⃣ Время аукциона: <b>{data.get('auction_timeout_minutes', '—')} мин</b>\n"
        f"7️⃣ % выплаты оператору: <b>{data.get('operator_payout_percent', '—')}%</b>\n\n"
        "Нажмите <b>Сохранить</b> или <b>Начать заново</b>"
    )


@router.callback_query(WizardCB.filter(F.action == "save"), SetupWizardStates.confirming, IsOwner())
async def wizard_save(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    svc = SettingsService(session=session)

    await svc.set("service_name", str(data["service_name"]))
    await svc.set("welcome_text", str(data["welcome_text"]))
    await svc.set("support_contact", str(data.get("support_contact") or ""))
    await svc.set("payment_requisites", str(data.get("payment_requisites") or ""))
    await svc.set("max_active_orders", str(data["max_active_orders"]))
    await svc.set("auction_timeout_minutes", str(data["auction_timeout_minutes"]))
    await svc.set("operator_payout_percent", str(data["operator_payout_percent"]))

    await state.clear()
    await callback.message.edit_text(
        "✅ <b>Настройки сохранены!</b>\n\n"
        f"Сервис: <b>{html.escape(data['service_name'])}</b>\n"
        "Используйте кнопку «⚙️ Настройки» чтобы посмотреть текущие значения.",
        parse_mode="HTML",
    )
    await callback.message.answer(
        "Вы в главном меню владельца.",
        reply_markup=owner_main_kb(),
    )
    await callback.answer()


@router.callback_query(WizardCB.filter(F.action == "restart"), IsOwner())
async def wizard_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_text("🔄 Мастер перезапущен")
    await start_wizard(callback.message, state)


@router.message(SetupWizardStates.confirming, IsOwner())
async def wizard_confirming_fallback(message: Message) -> None:
    await message.answer(
        "👆 Нажмите кнопку <b>Сохранить</b> или <b>Начать заново</b> выше\n"
        "Для отмены — /cancel",
        parse_mode="HTML",
    )
