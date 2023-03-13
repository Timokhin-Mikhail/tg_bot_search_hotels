from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def city_key(citys) -> InlineKeyboardMarkup:
    destinations =InlineKeyboardMarkup()
    for city in citys:
        destinations.add(InlineKeyboardButton(text=city['city_name'],
                                          callback_data=city['city_id']))
    return destinations