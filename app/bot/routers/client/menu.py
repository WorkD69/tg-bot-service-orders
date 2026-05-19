import html as _html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.client_reply import (
    BTN_CREATE,
    BTN_CURRENT,
    BTN_HISTORY,
    BTN_HOW,
    BTN_REVIEWS,
    client_main_kb,
)
from app.bot.keyboards.operator_reply import operator_dm_kb
from app.bot.keyboards.owner_reply import owner_main_kb
from app.bot.filters import IsClient
from app.db.models.user import User, UserRole
from app.services.settings_service import SettingsService

router = Router()

# Fallback used only when BotSettings is unavailable (e.g. first deploy before migration)
_WELCOME_TEXT_FALLBACK = "👋 Привет, {name}! Здесь вы можете оставить заявку — выберите действие:"


def _main_kb(user: User):
    if user.role == UserRole.owner:
        return owner_main_kb()
    if user.role in (UserRole.operator, UserRole.admin):
        return operator_dm_kb()
    return client_main_kb()



# ── PRIMARY MENU BUTTONS ───────────────────────────────────────────────────────

@router.message(F.text == BTN_HOW, IsClient())
async def how_it_works(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    svc = SettingsService(session=session)
    support = await svc.get("support_contact")
    support_line = f"\n❓ Остались вопросы — мы на связи: {support}" if support else ""
    text = (
        "ℹ️ Как мы работаем:\n\n"
        "1️⃣ Вы создаёте заявку — описание задачи, дедлайн, желаемый бюджет\n"
        "2️⃣ Операторы делают ставки — вы получаете лучшую цену\n"
        "3️⃣ Вы оплачиваете удобным способом\n"
        "4️⃣ Оператор берёт задачу в работу\n"
        "5️⃣ Готовый результат приходит прямо сюда\n\n"
        "💬 Есть вопросы по результату — напишите оператору прямо в чате заявки\n"
        "⚠️ Не устраивает результат — нажмите «Оспорить», разберёмся"
        f"{support_line}"
    )
    await message.answer(text)


@router.message(F.text == BTN_CREATE, IsClient())
async def menu_create_order(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.clear()

    from app.repositories.order_repo import OrderRepo
    svc = SettingsService(session=session)
    max_orders = await svc.get_int("max_active_orders")
    active_orders = await OrderRepo(session).get_client_active_orders(user.id)
    if len(active_orders) >= max_orders:
        await message.answer(
            f"❌ У вас уже {max_orders} активных заявок\n"
            "Дождитесь завершения одной из них, прежде чем создавать новую",
            reply_markup=client_main_kb(),
        )
        return

    from app.bot.states.order_create import OrderCreateStates
    await state.set_state(OrderCreateStates.waiting_files)
    await state.update_data(files=[])
    await message.answer(
        "📎 Прикрепите файлы к заявке (до 10 штук)\n"
        "Когда закончите — отправьте /done\n"
        "Для отмены — /cancel"
    )


@router.message(F.text == BTN_CURRENT, IsClient())
async def menu_current_orders(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.clear()

    from app.repositories.order_repo import OrderRepo
    from app.bot.keyboards.order_inline import client_orders_list_kb
    orders = await OrderRepo(session).get_client_active_orders(user.id)
    if not orders:
        await message.answer("📭 У вас нет активных заявок")
        return
    await message.answer("📋 Ваши текущие заявки:", reply_markup=client_orders_list_kb(orders))


@router.message(F.text == BTN_HISTORY, IsClient())
async def menu_history_orders(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.clear()

    from app.repositories.order_repo import OrderRepo
    from app.bot.keyboards.order_inline import client_orders_list_kb
    orders = await OrderRepo(session).get_client_history(user.id)
    if not orders:
        await message.answer("📭 История заявок пуста")
        return
    await message.answer("🗂 История заявок:", reply_markup=client_orders_list_kb(orders))


@router.message(F.text == BTN_REVIEWS, IsClient())
async def menu_reviews(message: Message, state: FSMContext):
    await state.clear()

    from app.bot.keyboards.admin_inline import reviews_menu_kb
    await message.answer("⭐ Отзывы:", reply_markup=reviews_menu_kb())

