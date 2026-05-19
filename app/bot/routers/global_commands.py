"""Global command handlers — registered first in the dispatcher.

By being included before all role-specific routers, these handlers fire even
when the user is inside an FSM state (wizard, bid, messaging, file upload, etc.).
This prevents slash commands from being swallowed as plain text by FSM handlers.
"""
import html as _html

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.client_reply import client_main_kb
from app.bot.keyboards.operator_reply import operator_dm_kb
from app.bot.keyboards.owner_reply import owner_main_kb
from app.db.models.user import User, UserRole

router = Router()

_WELCOME_TEXT_FALLBACK = "👋 Привет, {name}! Здесь вы можете оставить заявку — выберите действие:"


def _main_kb(user: User):
    if user.role == UserRole.owner:
        return owner_main_kb()
    if user.role in (UserRole.operator, UserRole.admin):
        return operator_dm_kb()
    return client_main_kb()


@router.message(Command("cancel"))
async def global_cancel(message: Message, state: FSMContext, user: User):
    current = await state.get_state()
    if current is None:
        await message.answer("ℹ️ Нет активного действия для отмены")
        return
    await state.clear()
    await message.answer("✅ Действие отменено", reply_markup=_main_kb(user))


@router.message(CommandStart())
async def global_start(
    message: Message,
    user: User,
    state: FSMContext,
    session: AsyncSession,
):
    current = await state.get_state()
    await state.clear()
    if current is not None:
        await message.answer(
            "ℹ️ Незавершённое действие отменено\n"
            "Используйте /cancel в любое время чтобы прервать текущее действие"
        )

    if user.role == UserRole.owner:
        await message.answer(
            f"👋 Привет, {user.full_name}! Ты — владелец сервиса.\n\n"
            "⚙️ Управляй настройками через меню ниже\n"
            "🧙 Для первичной настройки запусти мастер",
            reply_markup=owner_main_kb(),
        )
    elif user.role in (UserRole.operator, UserRole.admin):
        await message.answer(
            f"👋 Привет, {user.full_name}! Ты в режиме оператора\n\n"
            "📋 Работай с заявками через кнопки — также можешь создавать заявки как клиент",
            reply_markup=operator_dm_kb(),
        )
    else:
        from app.services.settings_service import SettingsService
        svc = SettingsService(session=session)
        welcome_raw = await svc.get("welcome_text")
        safe_name = _html.escape(user.full_name)
        welcome = (
            welcome_raw.replace("{name}", safe_name)
            if welcome_raw
            else _WELCOME_TEXT_FALLBACK.format(name=safe_name)
        )
        await message.answer(welcome, reply_markup=client_main_kb())
