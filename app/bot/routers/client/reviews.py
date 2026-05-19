from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

import html as _html

from app.bot.filters import IsClient
from app.bot.keyboards.admin_inline import rating_kb
from app.bot.keyboards.callbacks import OrderCB, RatingCB, ReviewListCB  # ReviewListCB kept for "all" handler
from app.bot.keyboards.client_reply import client_main_kb
from app.bot.states.note import ReviewStates
from app.config import settings  # used for admin_telegram_id
from app.db.models.order import OrderStatus
from app.db.models.user import User, UserRole

from app.repositories.order_repo import OrderRepo
from app.repositories.review_repo import ReviewRepo

router = Router()

REVIEWS_PAGE_SIZE = 5
MAX_REVIEW_LEN = 1000


@router.callback_query(ReviewListCB.filter(F.action == "all"))
async def all_reviews(callback: CallbackQuery, callback_data: ReviewListCB, session: AsyncSession):
    from app.bot.keyboards.admin_inline import reviews_pagination_kb
    reviews = await ReviewRepo(session).get_approved()
    if not reviews:
        await callback.answer("📭 Пока нет одобренных отзывов", show_alert=True)
        return

    total_pages = max(1, (len(reviews) + REVIEWS_PAGE_SIZE - 1) // REVIEWS_PAGE_SIZE)
    page = max(0, min(callback_data.page, total_pages - 1))
    page_reviews = reviews[page * REVIEWS_PAGE_SIZE:(page + 1) * REVIEWS_PAGE_SIZE]

    lines = []
    for r in page_reviews:
        name = _html.escape(r.client.full_name)
        stars = "⭐" * r.rating
        lines.append(f"{stars} {name}:\n{_html.escape(r.text)}")

    header = f"⭐ Отзывы ({page + 1}/{total_pages}):" if total_pages > 1 else "⭐ Отзывы:"
    text = header + "\n\n" + "\n\n".join(lines)
    kb = reviews_pagination_kb(page, total_pages)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass  # MessageNotModified — already on this page
    await callback.answer()



# ── Leave review FSM ──────────────────────────────────────────────────────────

@router.callback_query(OrderCB.filter(F.action == "review"), IsClient())
async def start_review(
    callback: CallbackQuery,
    callback_data: OrderCB,
    state: FSMContext,
    session: AsyncSession,
    user: User,
):
    order = await OrderRepo(session).get_by_id(callback_data.order_id)
    if not order or order.client_id != user.id:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    if order.status != OrderStatus.completed:
        await callback.answer("⚠️ Отзыв можно оставить только по выполненной заявке", show_alert=True)
        return

    existing = await ReviewRepo(session).get_by_order_client(order.id, user.id)
    if existing:
        await callback.answer("ℹ️ Вы уже оставили отзыв по этой заявке", show_alert=True)
        return

    await state.set_state(ReviewStates.waiting_rating)
    await state.update_data(order_id=order.id)
    await callback.message.answer(
        "⭐ Оцените работу оператора:",
        reply_markup=rating_kb(order.id),
    )
    await callback.answer()


@router.callback_query(RatingCB.filter(), ReviewStates.waiting_rating, IsClient())
async def got_rating(
    callback: CallbackQuery,
    callback_data: RatingCB,
    state: FSMContext,
):
    await state.update_data(rating=callback_data.stars)
    await state.set_state(ReviewStates.waiting_text)
    stars = "⭐" * callback_data.stars
    await callback.message.answer(f"✅ Оценка {stars} выбрана\n\n✍️ Напишите ваш отзыв:")
    await callback.answer()


@router.message(ReviewStates.waiting_rating, IsClient())
async def rating_unexpected_input(message: Message):
    await message.answer(
        "⭐ Пожалуйста, выберите оценку нажав на одну из кнопок выше\n"
        "Для отмены — /cancel"
    )


@router.message(ReviewStates.waiting_text, F.text, IsClient())
async def got_review_text(
    message: Message, state: FSMContext, session: AsyncSession, user: User, post_commit: list
):
    text = message.text.strip()
    if not text:
        await message.answer(
            "✍️ Отзыв не может быть пустым — напишите несколько слов\n"
            "Для отмены — /cancel"
        )
        return
    if len(text) > MAX_REVIEW_LEN:
        await message.answer(
            f"❌ Слишком длинный отзыв ({len(text)} символов)\n"
            f"Максимум {MAX_REVIEW_LEN} символов — сократите текст"
        )
        return

    data = await state.get_data()
    order_id: int = data["order_id"]
    rating: int = data.get("rating", 5)

    # Idempotent create: returns (review, is_new=False) if review already exists
    review, is_new = await ReviewRepo(session).create(
        order_id=order_id, client_id=user.id, text=text, rating=rating,
    )
    await state.clear()

    # Only show client reply keyboard for actual clients — operators/admins don't use it
    reply_kb = client_main_kb() if user.role == UserRole.client else None

    if is_new:
        # Defer admin notification — fires after commit so admin sees a committed review
        from app.bot.keyboards.admin_inline import review_moderation_kb
        from app.bot.instance import bot
        safe_name = _html.escape(f"@{user.username}" if user.username else user.full_name)
        stars = "⭐" * rating
        admin_text = (
            f"📝 Новый отзыв от {safe_name} по заявке №{order_id} ({stars}):\n\n{_html.escape(review.text)}"
        )
        post_commit.append(bot.send_message(
            settings.admin_telegram_id,
            admin_text,
            reply_markup=review_moderation_kb(review.id),
        ))
        await message.answer("🙏 Спасибо за обратную связь!", reply_markup=reply_kb)
    else:
        # Duplicate submit — no new admin alert
        await message.answer(
            "ℹ️ Ваш отзыв уже получен и находится на модерации",
            reply_markup=reply_kb,
        )


@router.message(ReviewStates.waiting_text, ~F.text, IsClient())
async def review_text_unexpected_type(message: Message):
    await message.answer(
        "✍️ Напишите текст отзыва\n"
        "Для отмены — /cancel"
    )
