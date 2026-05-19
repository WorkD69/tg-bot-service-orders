"""Business-settings service.

Hierarchy (highest priority first):
    1. Redis cache  (TTL = CACHE_TTL seconds)
    2. PostgreSQL   (bot_settings table)
    3. DEFAULTS     (hardcoded fallback — never raises)

Redis is optional: if the client is None or any Redis operation raises,
the service degrades silently to DB-only mode.  The bot stays running.

Usage example (inside a handler):
    svc = SettingsService(session=session, redis=redis_client)
    name  = await svc.get("service_name")        # → str
    limit = await svc.get_int("max_active_orders") # → int
    pct   = await svc.get_float("operator_payout_percent") # → float
    await svc.set("welcome_text", "Hello!")
    all_  = await svc.get_all()                  # → dict[str, str]
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings_repo import SettingsRepo

logger = logging.getLogger(__name__)

# Redis cache key prefix and TTL (5 minutes)
_KEY_PREFIX = "bot_settings:"
CACHE_TTL = 300  # seconds


class SettingsService:
    """Typed accessor for runtime-configurable business parameters.

    Parameters
    ----------
    session:
        Active async SQLAlchemy session.  Required.
    redis:
        Optional ``redis.asyncio.Redis`` client.  When ``None`` (or when
        a Redis call fails), the service falls back to direct DB reads.
    """

    DEFAULTS: dict[str, str] = {
        "service_name": "Сервис заявок",
        "welcome_text": "Добро пожаловать! Выберите действие:",
        "support_contact": "",
        "payment_requisites": "",
        "max_active_orders": "5",
        "auction_timeout_minutes": "120",
        "operator_payout_percent": "70",
    }

    def __init__(self, session: AsyncSession, redis: Any = None) -> None:
        self._repo = SettingsRepo(session)
        self._redis = redis

    # ── Internal Redis helpers ────────────────────────────────────────────────

    async def _cache_get(self, key: str) -> str | None:
        """Try to get *key* from Redis. Returns None on any failure."""
        if self._redis is None:
            return None
        try:
            raw = await self._redis.get(f"{_KEY_PREFIX}{key}")
            if raw is None:
                return None
            # redis-py may return bytes or str depending on decode_responses setting
            return raw.decode("utf-8") if isinstance(raw, bytes) else raw
        except Exception:
            logger.debug("Redis cache_get failed for key=%r, falling back to DB", key)
            return None

    async def _cache_set(self, key: str, value: str) -> None:
        """Write *key*→*value* to Redis with TTL. Silently ignores failures."""
        if self._redis is None:
            return
        try:
            await self._redis.set(f"{_KEY_PREFIX}{key}", value, ex=CACHE_TTL)
        except Exception:
            logger.debug("Redis cache_set failed for key=%r, continuing without cache", key)

    async def _cache_delete(self, key: str) -> None:
        """Invalidate *key* in Redis. Silently ignores failures."""
        if self._redis is None:
            return
        try:
            await self._redis.delete(f"{_KEY_PREFIX}{key}")
        except Exception:
            logger.debug("Redis cache_delete failed for key=%r", key)

    # ── Public API ────────────────────────────────────────────────────────────

    async def get(self, key: str) -> str:
        """Return the value for *key*.

        Resolution order: Redis → DB → DEFAULTS.
        Never raises KeyError — falls back to empty string if key is unknown.
        """
        # 1. Redis
        cached = await self._cache_get(key)
        if cached is not None:
            return cached

        # 2. DB
        db_value = await self._repo.get(key)
        if db_value is not None:
            await self._cache_set(key, db_value)
            return db_value

        # 3. Hardcoded default
        return self.DEFAULTS.get(key, "")

    async def get_int(self, key: str) -> int:
        """Return the value for *key* as int.

        Falls back to the default from DEFAULTS on parse error.
        """
        raw = await self.get(key)
        try:
            return int(raw)
        except (ValueError, TypeError):
            default_raw = self.DEFAULTS.get(key, "0")
            try:
                return int(default_raw)
            except (ValueError, TypeError):
                return 0

    async def get_float(self, key: str) -> float:
        """Return the value for *key* as float.

        Falls back to the default from DEFAULTS on parse error.
        """
        raw = await self.get(key)
        try:
            return float(raw)
        except (ValueError, TypeError):
            default_raw = self.DEFAULTS.get(key, "0")
            try:
                return float(default_raw)
            except (ValueError, TypeError):
                return 0.0

    async def set(self, key: str, value: str) -> None:
        """Persist *key*→*value* to DB and invalidate Redis cache."""
        await self._repo.upsert(key, str(value))
        await self._cache_delete(key)

    async def get_all(self) -> dict[str, str]:
        """Return all settings stored in the DB.

        Keys present in DEFAULTS but absent from DB are included with
        their default values so the owner sees a complete list.
        """
        db_rows = await self._repo.get_all()
        # Merge: DEFAULTS as base, DB values override
        merged = {**self.DEFAULTS, **db_rows}
        return merged
