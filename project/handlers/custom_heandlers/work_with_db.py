from peewee import *
import os
from loader import bot

text = os.path.abspath(os.path.join('database/search_history.db'))
db = SqliteDatabase(text)

class OneResult(Model):
    id = AutoField(null=False, unique=True, primary_key=True)
    user_id = IntegerField()
    time = DateTimeField()
    hotel_name = CharField()
    hotel_site = CharField()
    search_command = CharField()
    class Meta:
        database = db

# OneResult.create_table()

def get_info(ui):
    try:
        with db:
            results =[(ti, sc) for ti, sc in OneResult.select(OneResult.time, OneResult.search_command).where(OneResult.user_id == ui)\
                .group_by(OneResult.time, OneResult.search_command)\
                .order_by(OneResult.time.desc()).limit(5).tuples()]
            dict_for_user = dict()
            for result in results:
                dict_for_user.update({result: [i for i in OneResult.select(OneResult.hotel_name, OneResult.hotel_site)
                                     .where(OneResult.user_id == ui, OneResult.time == result[0], OneResult.search_command == result[1]).tuples()\
                ]})
            for key, values in dict_for_user.items():
                text_list = []
                for i in values:
                    text_list.append(f'Отель: {i[0]}, ссылка на отель: {i[1]}')
                text_list = '\n'.join(text_list)
                good_text = f"Поиск от {key[0]} по команде: {key[1]}:\n {text_list}"
                bot.send_message(ui, f'{good_text}')
    except:
        bot.send_message(ui, f'Не удалось загрузить историю')





def upload_info(ui: int, time:str, command: str, all_hotel: list):
    for_upload = [(ui, i[1], time, i[5], command) for i in all_hotel]
    fields = [OneResult.user_id, OneResult.hotel_name, OneResult.time, OneResult.hotel_site, OneResult.search_command]
    with db.atomic():
        OneResult.insert_many(for_upload, fields=fields).execute()


# upload_info(1, 'hotel', str(datetime.now()), 'site', 'exit')
# get_info()
