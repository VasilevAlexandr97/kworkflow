from aiogram.fsm.state import State, StatesGroup


class FreelancerProfileState(StatesGroup):
    edit = State()


class StopWordsState(StatesGroup):
    add = State()
    delete = State()


class PaymentState(StatesGroup):
    set_email = State()
