from aiogram.fsm.state import State, StatesGroup


class FreelancerProfileState(StatesGroup):
    edit = State()


class StopWordsState(StatesGroup):
    add = State()
    delete = State()
