"""Unit tests for setup wizard validation helpers.

Tests are purely synchronous — no DB or Telegram needed.
"""
import pytest

from app.bot.routers.owner.setup_wizard import (
    _validate_auction_timeout,
    _validate_max_orders,
    _validate_operator_payout,
    _validate_payment_requisites,
    _validate_service_name,
    _validate_support_contact,
    _validate_welcome_text,
)


# ── service_name ─────────────────────────────────────────────────────────────

class TestServiceName:
    def test_valid_short(self):
        assert _validate_service_name("Ремонт") == "Ремонт"

    def test_valid_64_chars(self):
        v = "A" * 64
        assert _validate_service_name(v) == v

    def test_strips_whitespace(self):
        assert _validate_service_name("  Сервис  ") == "Сервис"

    def test_empty_rejected(self):
        assert _validate_service_name("") is None

    def test_whitespace_only_rejected(self):
        assert _validate_service_name("   ") is None

    def test_65_chars_rejected(self):
        assert _validate_service_name("A" * 65) is None


# ── welcome_text ──────────────────────────────────────────────────────────────

class TestWelcomeText:
    def test_valid(self):
        assert _validate_welcome_text("Добро пожаловать!") == "Добро пожаловать!"

    def test_500_chars_ok(self):
        v = "X" * 500
        assert _validate_welcome_text(v) == v

    def test_501_chars_rejected(self):
        assert _validate_welcome_text("X" * 501) is None

    def test_empty_rejected(self):
        assert _validate_welcome_text("") is None


# ── support_contact ───────────────────────────────────────────────────────────

class TestSupportContact:
    def test_valid_handle(self):
        ok, v = _validate_support_contact("@myshop_support")
        assert ok is True
        assert v == "@myshop_support"

    def test_dash_maps_to_empty(self):
        ok, v = _validate_support_contact("-")
        assert ok is True
        assert v == ""

    def test_empty_string_ok(self):
        ok, v = _validate_support_contact("")
        assert ok is True
        assert v == ""

    def test_handle_too_short_rejected(self):
        """@abcd is only 4 chars after @, minimum is 5."""
        ok, _ = _validate_support_contact("@abcd")
        assert ok is False

    def test_no_at_sign_rejected(self):
        ok, _ = _validate_support_contact("myshop_support")
        assert ok is False

    def test_plain_text_rejected(self):
        ok, _ = _validate_support_contact("support@email.com")
        assert ok is False

    def test_valid_handle_with_digits(self):
        ok, v = _validate_support_contact("@support123")
        assert ok is True
        assert v == "@support123"


# ── payment_requisites ────────────────────────────────────────────────────────

class TestPaymentRequisites:
    def test_valid_text(self):
        assert _validate_payment_requisites("Сбербанк: 4276 1234 5678") == "Сбербанк: 4276 1234 5678"

    def test_dash_maps_to_empty(self):
        assert _validate_payment_requisites("-") == ""

    def test_empty_string_ok(self):
        assert _validate_payment_requisites("") == ""

    def test_1000_chars_ok(self):
        assert _validate_payment_requisites("R" * 1000) == "R" * 1000

    def test_1001_chars_rejected(self):
        assert _validate_payment_requisites("R" * 1001) is None


# ── max_active_orders ─────────────────────────────────────────────────────────

class TestMaxOrders:
    def test_valid_5(self):
        assert _validate_max_orders("5") == 5

    def test_valid_1(self):
        assert _validate_max_orders("1") == 1

    def test_valid_20(self):
        assert _validate_max_orders("20") == 20

    def test_zero_rejected(self):
        assert _validate_max_orders("0") is None

    def test_21_rejected(self):
        assert _validate_max_orders("21") is None

    def test_negative_rejected(self):
        assert _validate_max_orders("-1") is None

    def test_text_rejected(self):
        assert _validate_max_orders("пять") is None

    def test_float_rejected(self):
        assert _validate_max_orders("5.5") is None


# ── auction_timeout_minutes ───────────────────────────────────────────────────

class TestAuctionTimeout:
    def test_valid_120(self):
        assert _validate_auction_timeout("120") == 120

    def test_valid_10_min(self):
        assert _validate_auction_timeout("10") == 10

    def test_valid_1440_max(self):
        assert _validate_auction_timeout("1440") == 1440

    def test_9_rejected(self):
        assert _validate_auction_timeout("9") is None

    def test_1441_rejected(self):
        assert _validate_auction_timeout("1441") is None

    def test_zero_rejected(self):
        assert _validate_auction_timeout("0") is None

    def test_text_rejected(self):
        assert _validate_auction_timeout("two hours") is None


class TestOperatorPayout:
    def test_valid_70(self):
        assert _validate_operator_payout("70") == 70

    def test_valid_0_min(self):
        assert _validate_operator_payout("0") == 0

    def test_valid_100_max(self):
        assert _validate_operator_payout("100") == 100

    def test_negative_rejected(self):
        assert _validate_operator_payout("-1") is None

    def test_101_rejected(self):
        assert _validate_operator_payout("101") is None

    def test_float_rejected(self):
        assert _validate_operator_payout("70.5") is None

    def test_text_rejected(self):
        assert _validate_operator_payout("seventy") is None
