from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def make_but_yes_or_no() -> InlineKeyboardMarkup:
    choice_but = InlineKeyboardMarkup()
    choice_but.add(InlineKeyboardButton(text='Да', callback_data='1'))
    choice_but.add(InlineKeyboardButton(text='Нет', callback_data='0'))
    return choice_but
