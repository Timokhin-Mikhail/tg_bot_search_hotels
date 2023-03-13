from telebot.types import Message, InputMediaPhoto

from loader import bot


@bot.message_handler(state=[None], commands=['exit'])
def bot_exit(message: Message):
    bot.reply_to(message, f"Указанная команда используется для выхода из поиска\n"
                          f"Её необходимо использовать только тогда, когда поиск отеля уже начат,"
                          f" но вы не желаете его продолжать")
