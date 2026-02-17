from aiogram.fsm.state import State, StatesGroup

class OrderInfo(StatesGroup):
    tg_nickname = State()
    name = State()
    phone = State()
    type_rug = State()
    color_rug = State()
    edging_rug = State()
    size_rug = State()