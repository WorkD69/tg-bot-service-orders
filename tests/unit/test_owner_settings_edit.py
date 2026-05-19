from app.bot.keyboards.owner_inline import owner_settings_kb
from app.bot.routers.owner.settings import validate_setting_value


def _button_texts() -> list[str]:
    return [button.text for row in owner_settings_kb().inline_keyboard for button in row]


def test_owner_settings_keyboard_has_single_setting_buttons() -> None:
    texts = _button_texts()

    assert "🏷 Изменить название" in texts
    assert "👋 Изменить приветствие" in texts
    assert "📞 Изменить контакт" in texts
    assert "💳 Изменить реквизиты" in texts
    assert "📦 Изменить лимит заявок" in texts
    assert "⏱ Изменить время аукциона" in texts
    assert "💰 Изменить % выплаты" in texts
    assert "🧙 Изменить все настройки" in texts


def test_validate_setting_value_reuses_service_name_rules() -> None:
    ok, value, _ = validate_setting_value("service_name", "  Бурмалда  ")

    assert ok is True
    assert value == "Бурмалда"


def test_validate_setting_value_rejects_bad_operator_payout() -> None:
    ok, value, error = validate_setting_value("operator_payout_percent", "101")

    assert ok is False
    assert value == ""
    assert "0 до 100" in error


def test_validate_setting_value_accepts_empty_requisites() -> None:
    ok, value, _ = validate_setting_value("payment_requisites", "-")

    assert ok is True
    assert value == ""
