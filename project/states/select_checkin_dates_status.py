from telebot.handler_backends import State, StatesGroup


class SelectCheckinDate(StatesGroup):
    date_in = State()
    date_out = State()
