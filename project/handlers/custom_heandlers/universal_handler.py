from telebot.types import Message, InputMediaPhoto
from states.universal_status import UniversalStatus
from keyboards.inline import choice_but_yes_or_no
from keyboards.inline import city_keyboard
from utils.work_with_float_like_str import isfloat, clining_str_with_float
from loader import bot
from config_data import config
import requests
import json
from datetime import datetime, date, timedelta
from handlers.custom_heandlers.work_with_db import upload_info


@bot.message_handler(state="*", commands=['exit'])
def any_state(message: Message):
    """
    Сброс состояния
    """
    bot.send_message(message.chat.id, 'Выход из поиска')
    bot.delete_state(message.from_user.id, message.chat.id)


def api_request(url,  # Меняется в зависимости от запроса.
                params,  # Параметры
                method_type,  # Метод\тип запроса GET\POST
                attempt=0):

    # В зависимости от типа запроса вызываем соответствующую функцию
    headers = {
        "X-RapidAPI-Key": f"{config.RAPID_API_KEY}",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"}
    posr_headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": f"{config.RAPID_API_KEY}",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    if method_type == 'GET':
        return get_request(url=url, params=params, headers=headers, attempt=attempt)
    else:
        return post_request(url=url, params=params, headers=posr_headers, attempt=attempt)


def get_request(url, params, headers, attempt):
    try:
        response = requests.request("GET", url, headers=headers, params=params, timeout=20)
        if response.status_code == requests.codes.ok and not ('errors' in response):
            return response.text
        elif attempt < 3:
            attempt += 1
            return get_request(url, params, headers, attempt)
        else:
            return '{}'
    except:
        return '{}'


def post_request(url, params, headers, attempt):
    try:
        response = requests.request("POST", url, json=params, headers=headers, timeout=20)
        if response.status_code == requests.codes.ok and not ('errors' in response):
            return response.text
        elif attempt < 3:
            attempt += 1
            return post_request(url, params, headers, attempt)
        else:
            return '{}'
    except:
        return '{}'


def city_founding(city):
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"
    querystring = {"q": city, "locale": "ru_RU"}
    response = api_request(method_type="GET", url=url, params=querystring)
    response = json.loads(response)
    if response:
        cities = list()
        for dest in [i for i in response['sr'] if (i['type'] in ('CITY', 'NEIGHBORHOOD'))]:  # Обрабатываем результат
            cities.append({'city_name': dest['regionNames']['displayName'],
                           'city_id': dest['gaiaId']})
    return cities  # если нет городов и районов, то вызовет ошибку


def city_markup(city_name, message):
    try:
        cities = city_founding(city_name)  # Функция "city_founding" уже возвращает список словарей с нужным именем и id
        if len(cities) == 0:
            raise Exception
        elif len(cities) == 1:
            return cities[0]['city_name'], cities[0]['city_id']
        destinations = city_keyboard.city_key(cities)
        return destinations
    except:
        bot.send_message(message.from_user.id, 'Мы не нашли такого города')


def method_for_text_icheck_date(ui, mi):
    with bot.retrieve_data(ui, mi) as data:
        today = date.today()
        text = f'Если вы хотите поменять дату, то сначала воспользуйтесь командой "/exit" для выхода из поиска,' \
               f' а затем командой "/select_checkin_dates" для выбора даты отъезда'
        if not ('checkin_date' in data) or data['checkin_date'] < today:
            tomorrow = today + timedelta(days=1)
            data['checkin_date'] = today
            data['checkout_date'] = tomorrow
            bot.send_message(mi, f"Т.к. у нас нету ваших дат заезда/выезда или они устарели "
                                 f"по умолчанию датой заезда установлено сегодняшнее число "
                                 f"{today.strftime('%d.%m.%Y')}, а датой отъезда {tomorrow.strftime('%d.%m.%Y')}\n"
                                 f"{text}")
        else:
            bot.send_message(mi, f" датой заезда установлено сохраненное число "
                                 f"{data['checkin_date'].strftime('%d.%m.%Y')},"
                                 f" а датой отъезда {data['checkout_date'].strftime('%d.%m.%Y')}\n{text}")


def work_with_hotel_lit_id(hotel_list_id, i):
    hotel_id = i['id']
    hotel_distance = i['destinationInfo']['distanceFromDestination']['value']  # float
    hotel_price_one_day = i['price']['lead']['formatted']
    hotel_price_all_day = i['price']['displayMessages'][1]['lineItems'][0]['value']
    hotel_name = i['name']
    hotel_price_all_day = hotel_price_all_day[1: hotel_price_all_day.find(' ')]
    hotel_card = f'https://www.hotels.com/h{hotel_id}.Hotel-Information'
    hotel_list_id.append(
        [hotel_id, hotel_name, hotel_distance, hotel_price_one_day, hotel_price_all_day,
         hotel_card])


@bot.message_handler(func=lambda message: True, state=UniversalStatus.city)
def bot_get_city(message: Message):
    if message.text.strip().isalpha():
        location_dict = city_markup(f'{message.text.strip().title()}', message)
        if location_dict is None:
            bot.delete_state(message.from_user.id, message.chat.id)
        elif isinstance(location_dict, tuple):
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['city_id'] = int(location_dict[1])
            method_for_text_icheck_date(message.from_user.id, message.chat.id)
            bot.send_message(message.from_user.id, 'Сколько отелей найти?')
            bot.set_state(message.from_user.id, UniversalStatus.hotels_count, message.chat.id)
        else:
            bot.send_message(message.from_user.id, 'Уточните, пожалуйста:', reply_markup=location_dict)

    else:
        bot.send_message(message.from_user.id, 'Название города может состоять только из букв '
                                               '(без тире, пробелов и т.д.)')


@bot.callback_query_handler(func=lambda call: True, state=UniversalStatus.city)
def callback_worker_city(call):
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['city_id'] = int(call.data.strip())
    method_for_text_icheck_date(call.from_user.id, call.message.chat.id)
    bot.send_message(call.message.chat.id, 'Сколько отелей найти?')
    bot.set_state(call.from_user.id, UniversalStatus.hotels_count, call.message.chat.id)


@bot.message_handler(func=lambda message: True, state=UniversalStatus.hotels_count)
def bot_get_hotels_count(message: Message):
    if message.text.strip().isdigit() and int(message.text.strip()) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if int(message.text.strip()) > 10:
                data['count_hotels'] = 10
            else:
                data['count_hotels'] = int(message.text.strip())
        bot.send_message(message.from_user.id, 'Нужны фото?', reply_markup=choice_but_yes_or_no.make_but_yes_or_no())
    else:
        bot.send_message(message.from_user.id, 'Необходимое количество отелей вводится числами и должно быть больше 0')


@bot.callback_query_handler(func=lambda call: True, state=UniversalStatus.hotels_count)
def callback_worker_photo(call):
    if call.data == '1':
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['photo'] = 1
        bot.send_message(call.message.chat.id, 'Сколько фото нужно?')
        bot.set_state(call.from_user.id, UniversalStatus.photos_count, call.message.chat.id)
    else:
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['photo'] = 0
            data['count_photo'] = 0
            command = data['command']
        if not (command == 'lowprice' or command == 'highprice'):
            bot.set_state(call.from_user.id, UniversalStatus.price_flag, call.message.chat.id)
            bot.send_message(call.from_user.id, 'Будем задавать диапозон цен?',
                             reply_markup=choice_but_yes_or_no.make_but_yes_or_no())
        else:
            get_result(call.from_user.id, call.message.chat.id)


@bot.message_handler(func=lambda message: True, state=UniversalStatus.photos_count)
def bot_get_photos_count(message: Message):
    if message.text.strip().isdigit() and int(message.text.strip()) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            command = data['command']
            if int(message.text.strip()) > 10:
                data['count_photo'] = 10
            else:
                data['count_photo'] = int(message.text.strip())
        if not (command == 'lowprice' or command == 'highprice'):
            bot.set_state(message.from_user.id, UniversalStatus.price_flag, message.chat.id)
            bot.send_message(message.from_user.id, 'Будем задавать диапозон цен?',
                             reply_markup=choice_but_yes_or_no.make_but_yes_or_no())
        else:
            get_result(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.from_user.id, 'Необходимое количество фото вводится числами и должно быть больше 0')


# best deal parth
# запрос диапазона цен
@bot.callback_query_handler(func=lambda call: True, state=UniversalStatus.price_flag)
def callback_worker_price(call):
    if call.data == '1':
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['price_flag'] = 1
        bot.set_state(call.from_user.id, UniversalStatus.price_min, call.message.chat.id)
        bot.send_message(call.from_user.id, 'Введите минимальную стоимость отеля за ночь в $ (USD)')

    else:
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['price_flag'] = 0
        bot.set_state(call.from_user.id, UniversalStatus.distance_flag, call.message.chat.id)
        bot.send_message(call.from_user.id, 'Будем задавать диапозон расстояния до центра города?',
                         reply_markup=choice_but_yes_or_no.make_but_yes_or_no())


@bot.message_handler(func=lambda message: True, state=UniversalStatus.price_min)
def bot_get_min_price(message: Message):
    if message.text.strip().isdigit() and int(message.text.strip()) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['price_min'] = int(message.text.strip())
        bot.set_state(message.from_user.id, UniversalStatus.price_max, message.chat.id)
        bot.send_message(message.from_user.id, 'Введите максимальную стоимость отеля за ночь в $ (USD)')
    else:
        bot.send_message(message.from_user.id, 'Минимальная стоимость вводится целым числом и должна быть больше 0')


@bot.message_handler(func=lambda message: True, state=UniversalStatus.price_max)
def bot_get_max_price(message: Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if message.text.strip().isdigit() and int(message.text.strip()) > data['price_min']:
            data['price_max'] = int(message.text.strip())
            bot.set_state(message.from_user.id, UniversalStatus.distance_flag, message.chat.id)
            bot.send_message(message.from_user.id, 'Будем задавать диапозон расстояния до центра города?',
                             reply_markup=choice_but_yes_or_no.make_but_yes_or_no())
        else:
            bot.send_message(message.from_user.id, 'Минимальная стоимость вводится целым числом и должна быть больше'
                                                   ' ранее введеной минимальной суммы')


# работа с расстоянием до центра города
@bot.callback_query_handler(func=lambda call: True, state=UniversalStatus.distance_flag)
def callback_worker_distance(call):
    if call.data == '1':
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['distance_flag'] = 1
        bot.send_message(call.from_user.id, 'Введите минимальное растояние до центра города в километрах')
        bot.set_state(call.from_user.id, UniversalStatus.distance_min, call.message.chat.id)
    else:
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['distance_flag'] = 0
        get_result(call.from_user.id, call.message.chat.id)


@bot.message_handler(func=lambda message: True, state=UniversalStatus.distance_min)
def bot_get_min_distance(message: Message):
    if isfloat(message.text) and float(clining_str_with_float(message.text)) >= 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['distance_min'] = float(clining_str_with_float(message.text))
        bot.send_message(message.from_user.id, 'Введите максимальное растояние до центра города в километрах')
        bot.set_state(message.from_user.id, UniversalStatus.distance_max, message.chat.id)
    else:
        bot.send_message(message.from_user.id, 'Минимальная расстояние вводится числами и'
                                               ' должно быть больше или равно 0')


@bot.message_handler(func=lambda message: True, state=UniversalStatus.distance_max)
def bot_get_max_distance(message: Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if not(isfloat(message.text) and float(clining_str_with_float(message.text)) > data['distance_min']):
            distance = 0
        else:
            distance = clining_str_with_float(message.text)
            data['distance_max'] = float(distance)

    if not distance:
        bot.send_message(message.from_user.id, 'Минимальная стоимость вводится числами и должна быть больше'
                                               ' ранее введеной минимальной суммы')
    else:
        get_result(message.from_user.id, message.chat.id)


# метод, который выводит итоговый результат
def get_result(user_id, chat_id):
    try:
        with bot.retrieve_data(user_id, chat_id) as data:
            year_in, month_in, day_in = data['checkin_date'].year, data['checkin_date'].month, data['checkin_date'].day
            year_out, month_out, day_out = data['checkout_date'].year, data['checkout_date'].month,\
                data['checkout_date'].day
            url = "https://hotels4.p.rapidapi.com/properties/v2/list"
            payload = {
                "currency": "USD",
                "eapid": 1,
                "locale": "ru_RU",
                "siteId": 300000001,
                "destination": {
                    "regionId": f"{data['city_id']}"
                },
                "checkInDate": {
                    "day": day_in,
                    "month": month_in,
                    "year": year_in
                },
                "checkOutDate": {
                    "day": day_out,
                    "month": month_out,
                    "year": year_out
                },
                "rooms": [{"adults": 1, "children": []}],
                "resultsStartingIndex": 0,
                "resultsSize": int(data['count_hotels']),
                "sort": "PRICE_LOW_TO_HIGH"
                }
            photo_flag, count_hotels, price_flag, distance_flag, command_tag = \
                data['photo'], data['count_hotels'], data['price_flag'], data['distance_flag'], data['command']
            if command_tag == 'highprice':
                payload["sort"] = "PRICE_HIGH_TO_LOW"
            elif command_tag == 'bestdeal':
                payload["resultsSize"] = payload["resultsSize"] * 3
            if photo_flag:
                count_photo = data['count_photo']
            if distance_flag:
                distance_min, distance_max = data['distance_min'], data['distance_max']
            if price_flag:
                price_min, price_max = data['price_min'], data['price_max']
                payload.update({"filters": {"price": {"max": price_max, "min": price_min}}})
        response = api_request(method_type="POST", url=url, params=payload)
        response = json.loads(response)
        hotel_list_id = list()
        if command_tag in ('lowprice', 'highprice'):
            for i in response['data']['propertySearch']['properties']:
                work_with_hotel_lit_id(hotel_list_id, i)
        else:
            search_flag = False
            while len(hotel_list_id) < count_hotels:
                response = api_request(method_type="POST", url=url, params=payload)
                response = json.loads(response)
                if not response or 'errors' in response:
                    break
                for i in response['data']['propertySearch']['properties']:
                    hotel_distance = i['destinationInfo']['distanceFromDestination']['value']
                    if (not distance_flag or distance_min <= hotel_distance <= distance_max) and len(
                            hotel_list_id) < count_hotels:
                        work_with_hotel_lit_id(hotel_list_id, i)
                    elif hotel_distance > distance_max:
                        search_flag = True
                        break
                if search_flag:
                    break
                else:
                    payload['resultsStartingIndex'] += payload['resultsSize']
            if not hotel_list_id:
                bot.delete_state(user_id, chat_id)
                return bot.send_message(user_id, 'Отелей с заданными параметрами не нашлось')
        # дальше работаем с конкретными отелями
        url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

        for hotel in hotel_list_id:
            payload = {
                    "currency": "USD",
                    "eapid": 1,
                    "locale": "en_US",
                    "siteId": 300000001,
                    "propertyId": str(hotel[0])
                }
            response = api_request(method_type="POST", url=url, params=payload)
            response = json.loads(response)
            hotel.append(response['data']['propertyInfo']['summary']['location']['address']['addressLine'])
            if photo_flag:
                photo_list = list()
                search_photo = response['data']['propertyInfo']['propertyGallery']['images']
                for photo_dict in search_photo[0: count_photo]:
                    photo_list.append(photo_dict['image']['url'])
                hotel.append(photo_list)
        bot.send_message(user_id, 'Результаты поиска:')
        for hotel in hotel_list_id:
            text = f'Отель: {hotel[1]}\n' \
                   f'Адрес отеля: {hotel[6]}\n' \
                   f'Расстояние до центра города: {hotel[2]} км.\n' \
                   f'Цена за ночь: {hotel[3]}\n' \
                   f'Цена за всё время пребывания (включая налоги): {hotel[4]}\n'
            bot.send_message(user_id, text)
            if photo_flag:
                photo_good_type = [InputMediaPhoto(i) for i in hotel[7]]
                bot.send_media_group(chat_id, photo_good_type)
    except Exception as ex:
        bot.send_message(user_id, 'Возникли проблемы при получени данных с сервера')
        print(ex)
    else:
        try:
            search_time = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
            upload_info(user_id, search_time, "/lowprice", hotel_list_id)
        except:
            bot.send_message(user_id, 'Не удалось сохранить результаты этого поиска в историю')
    bot.delete_state(user_id, chat_id)


@bot.message_handler(func=lambda message: True, commands=['lowprice'])
def bot_lowprice(message: Message):
    bot.send_message(message.from_user.id, 'Введите город, в котором будем искать отели')
    bot.set_state(message.from_user.id, UniversalStatus.city, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = 'lowprice'
        data['price_flag'] = 0
        data['distance_flag'] = 0


@bot.message_handler(state="*", func=lambda message: True, commands=['bestdeal'])
def bot_bestdeal(message: Message):
    bot.send_message(message.from_user.id, 'Введите город, в котором будем искать отели')
    bot.set_state(message.from_user.id, UniversalStatus.city, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = 'bestdeal'


@bot.message_handler(state="*", func=lambda message: True, commands=['highprice'])
def bot_highprice(message: Message):
    bot.send_message(message.from_user.id, 'Введите город, в котором будем искать отели')
    bot.set_state(message.from_user.id, UniversalStatus.city, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = 'highprice'
        data['price_flag'] = 0
        data['distance_flag'] = 0
