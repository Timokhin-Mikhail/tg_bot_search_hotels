from telebot.handler_backends import State, StatesGroup


class UniversalStatus(StatesGroup):
    city = State()
    hotels_count = State()
    photos_count = State()
    result = State()
    price_flag = State()
    price_min = State()
    price_max = State()
    distance_flag = State()
    distance_min = State()
    distance_max = State()

