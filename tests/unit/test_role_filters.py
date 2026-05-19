from types import SimpleNamespace

import pytest

from app.bot.filters import IsOperator
from app.db.models.user import UserRole


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (UserRole.operator, True),
        (UserRole.admin, True),
        (UserRole.owner, True),
        (UserRole.client, False),
    ],
)
async def test_is_operator_allows_order_management_roles(role: UserRole, expected: bool) -> None:
    user = SimpleNamespace(role=role)

    assert await IsOperator()(event=None, user=user) is expected
