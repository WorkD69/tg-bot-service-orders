from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.db.models.user import User, UserRole


class IsOwner(BaseFilter):
    """Passes only for users with role=owner.

    Owner is a separate, dedicated role — distinct from admin.
    One user = one role: a user cannot be both owner and admin simultaneously.

    The owner role is assigned via /addowner (admin command) and grants access
    to the business-settings management interface (Setup Wizard, future step).
    """

    async def __call__(self, event: Message | CallbackQuery, user: User | None = None) -> bool:
        if user is None:
            return False
        return user.role == UserRole.owner
