from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bot_settings import BotSettings


class SettingsRepo:
    """Low-level DB access for the bot_settings table.

    All values are plain strings — type coercion is the caller's responsibility
    (SettingsService wraps this with typed helpers).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        """Return the value for *key*, or None if the key doesn't exist."""
        result = await self.session.execute(
            select(BotSettings.value).where(BotSettings.key == key)
        )
        return result.scalar_one_or_none()

    async def upsert(self, key: str, value: str) -> None:
        """Insert or update a setting. Uses PostgreSQL ON CONFLICT DO UPDATE."""
        stmt = (
            pg_insert(BotSettings)
            .values(key=key, value=value)
            .on_conflict_do_update(
                index_elements=["key"],
                set_={"value": value, "updated_at": func.now()},
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_all(self) -> dict[str, str]:
        """Return all settings as a plain dict."""
        result = await self.session.execute(
            select(BotSettings.key, BotSettings.value).order_by(BotSettings.key)
        )
        return {row.key: row.value for row in result}
