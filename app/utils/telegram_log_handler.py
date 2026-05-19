"""Custom logging handler that sends ERROR+ records to a Telegram chat.

Only fires when there is a running asyncio event loop (i.e. while the bot is
serving requests). Startup/shutdown errors won't be delivered but they will
still appear in docker-compose logs.
"""
import asyncio
import hashlib
import html
import logging
import time


class TelegramErrorHandler(logging.Handler):
    """Send ERROR and above to the given Telegram chat via HTTP."""

    def __init__(self, bot_token: str, chat_id: int, cooldown_seconds: int = 300) -> None:
        super().__init__(level=logging.ERROR)
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._chat_id = chat_id
        self._cooldown_seconds = cooldown_seconds
        self._last_sent_by_fingerprint: dict[str, float] = {}
        self.setFormatter(logging.Formatter(
            "%(name)s:%(lineno)d\n%(message)s",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            formatted = self.format(record)
            if self._is_rate_limited(formatted):
                return

            loop = asyncio.get_running_loop()
            loop.create_task(self._send(formatted))
        except RuntimeError:
            pass  # No event loop running - skip silently

    def _is_rate_limited(self, text: str) -> bool:
        """Suppress repeated identical errors so admin DMs do not become a flood."""
        if self._cooldown_seconds <= 0:
            return False

        now = time.monotonic()
        fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
        last_sent_at = self._last_sent_by_fingerprint.get(fingerprint)
        if last_sent_at is not None and now - last_sent_at < self._cooldown_seconds:
            return True

        self._last_sent_by_fingerprint[fingerprint] = now
        if len(self._last_sent_by_fingerprint) > 512:
            oldest = min(self._last_sent_by_fingerprint, key=self._last_sent_by_fingerprint.get)
            self._last_sent_by_fingerprint.pop(oldest, None)
        return False

    async def _send(self, text: str) -> None:
        import aiohttp
        body = (
            f"⚠️ <b>Ошибка бота</b>\n\n"
            f"<pre>{html.escape(text[:3800])}</pre>"
        )
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self._url,
                    json={
                        "chat_id": self._chat_id,
                        "text": body,
                        "parse_mode": "HTML",
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                )
        except Exception:
            pass  # Never raise from inside a log handler
