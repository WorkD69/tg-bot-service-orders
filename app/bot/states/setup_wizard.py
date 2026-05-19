from aiogram.fsm.state import State, StatesGroup


class SetupWizardStates(StatesGroup):
    """Owner setup wizard - 7 input steps + 1 confirm step."""

    waiting_service_name = State()        # step 1
    waiting_welcome_text = State()        # step 2
    waiting_support_contact = State()     # step 3
    waiting_payment_requisites = State()  # step 4
    waiting_max_orders = State()          # step 5
    waiting_auction_timeout = State()     # step 6
    waiting_operator_payout = State()     # step 7
    confirming = State()                  # step 8: show summary -> save / restart
