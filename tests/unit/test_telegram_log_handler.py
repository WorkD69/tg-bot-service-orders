import logging

from app.utils.telegram_log_handler import TelegramErrorHandler


def _record(message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="aiogram.dispatcher",
        level=logging.ERROR,
        pathname=__file__,
        lineno=225,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_repeated_error_is_rate_limited() -> None:
    handler = TelegramErrorHandler("token", 123, cooldown_seconds=300)
    text = handler.format(_record("Failed to fetch updates"))

    assert handler._is_rate_limited(text) is False
    assert handler._is_rate_limited(text) is True


def test_distinct_errors_are_not_rate_limited() -> None:
    handler = TelegramErrorHandler("token", 123, cooldown_seconds=300)

    assert handler._is_rate_limited(handler.format(_record("first error"))) is False
    assert handler._is_rate_limited(handler.format(_record("second error"))) is False
