from aiogram.fsm.state import State, StatesGroup


class CreateUser(StatesGroup):
    username = State()
    # status = State()
    expire = State()
    data_limit = State()
    groups = State()
    # note = State()
