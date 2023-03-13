from handlers.custom_heandlers.work_with_db import get_info
from loader import bot
from telebot.types import Message

@bot.message_handler(state="*", func=lambda message: True, commands=['history'])
def bot_history(message: Message):
    bot.send_message(message.from_user.id, 'Ищем историю поиска...')
    get_info(message.from_user.id)
