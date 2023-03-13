from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot.types import Message, InlineKeyboardMarkup
from states.select_checkin_dates_status import SelectCheckinDate
from loader import bot
from config_data import config
from datetime import date, timedelta



@bot.message_handler(commands=['select_checkin_dates'])
def start(message):
    calendar, step = DetailedTelegramCalendar(locale='ru').build()
    bot.set_state(message.from_user.id, SelectCheckinDate.date_in, message.chat.id)
    bot.send_message(message.chat.id, f"Выберите дату заезда : ", reply_markup=calendar)

@bot.message_handler(func=lambda message: True, state=[SelectCheckinDate.date_in, SelectCheckinDate.date_out])
def start(message):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['checkin_date'] = today
        data['checkout_date'] = tomorrow
    bot.send_message(message.chat.id, f"Вы не выбрали дату\n"
                                      f"Окно выбора дат деактивировано\n"
                                      f"По умолчанию датой заезда установлено сегодняшнее число "
                                      f"{today.strftime('%d.%m.%Y')},"
                                      f" а датой отъезда {tomorrow.strftime('%d.%m.%Y')}")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=SelectCheckinDate.date_in)
def cal(c):
    result, key, step = DetailedTelegramCalendar(locale='ru').process(c.data)
    if not result and key:
        bot.edit_message_text(f"Выберите дату заезда",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        if result < date.today():
            bot.send_message(c.message.chat.id, f"Дата заезда должна быть не раньше сегодняшней даты\n"
                                                f"выберете другую дату в том же календаре")
        else:
            with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
                data['checkin_date'] = result
            bot.set_state(c.from_user.id, SelectCheckinDate.date_out, c.message.chat.id)
            bot.edit_message_text(f"Датой заезда Вы выбрали {result.strftime('%d.%m.%Y')}",
                                  c.message.chat.id,
                                  c.message.message_id)
            calendar, step = DetailedTelegramCalendar(locale='ru').build()
            bot.send_message(c.message.chat.id, f"Выберите дату отъезда: ", reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=SelectCheckinDate.date_out)
def cal_2(c):
    result, key, step = DetailedTelegramCalendar(locale='ru').process(c.data)
    with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
        checkin_dates = data['checkin_date']
        if not result and key:
            bot.edit_message_text(f"Выберите дату отъезда",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            if result < checkin_dates:
                bot.send_message(c.message.chat.id, f"Дата отъезда должна быть не раньше даты заезда\n"
                                                    f"выберете другую дату в том же календаре")

            else:
                data['checkout_date'] = result
                bot.set_state(c.from_user.id, None, c.message.chat.id)
                bot.edit_message_text(f"Датой отъезда Вы выбрали {result.strftime('%d.%m.%Y')}",
                                      c.message.chat.id,
                                      c.message.message_id)


# bot.current_states.data[c.message.chat.id][ c.message.chat.id]['state']

