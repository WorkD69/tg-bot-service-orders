from aiogram.fsm.state import State, StatesGroup


class OwnerSettingsEditStates(StatesGroup):
    """Owner edits one settings value from the settings overview."""

    waiting_value = State()
