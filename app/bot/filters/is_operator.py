from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.db.models.user import User, UserRole


class IsOperator(BaseFilter):
    """Passes for users who can work with operator-facing order flows."""
    async def __call__(self, event: Message | CallbackQuery, user: User | None = None) -> bool:
        if user is None:
            return False
        return user.role in (UserRole.operator, UserRole.admin, UserRole.owner)
