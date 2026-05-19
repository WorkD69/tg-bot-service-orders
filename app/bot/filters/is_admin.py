from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.db.models.user import User, UserRole


class IsAdmin(BaseFilter):
    """Passes for admin and owner roles.

    Owner is treated as a superset of admin: the entrepreneur who deploys the bot
    should have full platform management capabilities without needing a separate account.
    Bootstrap: UserRegisterMiddleware auto-promotes admin_telegram_id → admin and
    owner_telegram_id → owner on first interaction.
    """
    async def __call__(self, event: Message | CallbackQuery, user: User | None = None) -> bool:
        if user is None:
            return False
        return user.role in (UserRole.admin, UserRole.owner)
