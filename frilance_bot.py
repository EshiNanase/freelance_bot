import os
import logging
import datetime
import environs
import requests

from enum import Enum, auto
from textwrap import dedent
from telegram import ParseMode
from django.conf import settings
from more_itertools import chunked
from telegram.ext import MessageFilter
from telegram import ReplyKeyboardMarkup
from telegram_bot.payment import send_payment_link
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)


logger = logging.getLogger(__name__)


class FilterAwesome(MessageFilter):
    def filter(self, message):
        return 'Взять в работу' in message.text or \
               'Подтвердить выполнение заказа' in message.text


check_do_to_work = FilterAwesome()


class FilterAnswer(MessageFilter):
    def filter(self, message):
        return 'Ответить исполнителю' in message.text


check_answer = FilterAnswer()


class States(Enum):
    START = auto()
    ADMIN = auto()
    PRICE = auto()
    ORDERS = auto()
    RATE_CHOIСE = auto()
    PAYMENT = auto()
    ORDER_NAME = auto()
    ORDER_DESCRIPTION = auto()
    ORDER_FILES = auto()
    CLIENT_ORDERS = auto()
    VERIFICATE = auto()
    FRILANCER = auto()
    FRILANCER_ORDERS = auto()
    ANSWER_TO_FRILANSER = auto()
    ORDERS_PAGINATOR = auto()


class BotData:
    ADMIN_CHAT_ID = 704859099


def call_api_get(endpoint):
    url = f"{settings.API_URL}/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def call_api_post(endpoint, payload):
    url = f"{settings.API_URL}/{endpoint}"
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


def start(update, context):
    user = update.effective_user
    greetings = dedent(fr'''
                            Приветствую {user.mention_markdown_v2()}\!
                            Я бот сервисной поддержки для PHP
                            Укажи свой статус\.''')

    message_keyboard = [["Клиент 😊", "Исполнитель 🥷"],
                        ['Написать администратору ✍️']]

    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_markdown_v2(text=greetings, reply_markup=markup)

    context.user_data['five_orders'] = ''
    context.user_data['count'] = 1
    return States.START


def message_to_admin(update, context):
    update.message.reply_text(text='Напишите вопрос администратору')
    return States.ADMIN


def send_to_admin(update, context):
    telegram_id = update.message.from_user.id
    message = update.message.text
    menu_msg = dedent(f"""\
                <b>Ваше сообщение отправлено администратору, он свяжется с вами в ближайшее время</b>

                <b>Ваше сообщение:</b>
                {message}
                """).replace("    ", "")
    update.message.reply_text(
        text=menu_msg,
        parse_mode=ParseMode.HTML
    )
    update.message.chat.id = BotData.ADMIN_CHAT_ID
    menu_msg = dedent(f"""\
                это видит администратор
                <b>ИД клиента:</b>
                {telegram_id}
                <b>Запрос:</b>
                {message}
                """).replace("    ", "")
    update.message.reply_text(
        text=menu_msg,
        parse_mode=ParseMode.HTML
    )
    return


def check_client(update, context):
    given_callback = update.callback_query
    if given_callback:
        telegram_id = context.user_data["telegram_id"]
        given_callback.answer()
        given_callback.delete_message()
    else:
        telegram_id = update.message.from_user.id
        context.user_data["telegram_id"] = telegram_id

    url = f"{settings.API_URL}/api/clients/{telegram_id}"
    response = requests.get(url)

    if response.ok:
        rest_days = response.json()['days_left']
        rest_orders = response.json()['requests_left']
        rate_name = response.json()['tariff_title']
        user_fullname = str(update.message.from_user['first_name']) + ' ' + str(
            update.message.from_user['last_name'])
        greetings = dedent(f'''
                        {user_fullname} вот информация по вашему тарифу:
                        Ваш тариф "{rate_name}"
                        Тариф действует до {rest_days}
                        В вашем тарифе осталось {rest_orders} запросов.''')

        message_keyboard = [["Новый заказ", "Мои заказы"]]
        markup = ReplyKeyboardMarkup(
            message_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )

        if given_callback:
            context.bot.reply_markdown_v2(
                text=greetings,
                chat_id=given_callback.message.chat.id,
                reply_markup=markup,
            )
            return States.ORDERS

        update.message.reply_text(text=greetings, reply_markup=markup)
        return States.ORDERS

    response = call_api_get('api/all_tariffs/')
    rates = response['tariffs']
    rates.extend(["Назад"])
    message_keyboard = list(chunked(rates, 2))

    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    with open('documents/Преимущества.pdf', 'rb') as image:
        price_pdf = image.read()

    greeting_msg = dedent("""\
        Привет!✌️

        Вы еще не зарегестрированы на нашем сайте. Для регистрации ознакомьтесь с нашим преимуществами\
         и выберите подходящий тариф, нажав на кнопку тарифа

        Это обязательная процедура, для продолжения пользования сайтом необходимо выбрать и оплатить тариф.
        """).replace("  ", "")
    update.message.reply_document(
        price_pdf,
        filename="Преимущества.pdf",
        caption=greeting_msg,
        reply_markup=markup)

    return States.PRICE


def chooze_rate(update, context):
    context.user_data["rate"] = update.message.text
    url = f"{settings.API_URL}/api/tariff/{update.message.text}"
    response = requests.get(url)
    response.raise_for_status()
    rate_name = response.json()['title']
    rate_description = response.json()['description']
    rate_quantity = response.json()['request_quantity']
    rate_price = response.json()['price']

    rate_message = dedent(f"""\
                        <b>Тариф</b>
                        {rate_name}
                        <b>Описание:</b>
                        {rate_description}
                        <b>Количество заявок в месяц:</b>
                        {rate_quantity}
                        <b>Стоимость тарифа:</b>
                        {rate_price}
                       """).replace("    ", "")

    message_keyboard = [
        ['Назад', 'Выбрать']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=rate_message,
                              reply_markup=markup,
                              parse_mode=ParseMode.HTML)
    return States.RATE_CHOIСE


def send_payment(update, context):
    message_keyboard = [
        ['Назад', 'Оплатить']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    chat_id = context.user_data["telegram_id"]
    tariff = context.user_data["rate"]
    update.message.reply_text(text=send_payment_link(chat_id, tariff),
                              reply_markup=markup)
    update.message.reply_text(text='жми оплатить',
                              reply_markup=markup)
    return States.PAYMENT


def add_user(update, context):
    payload = {
        "chat_id": context.user_data["telegram_id"],
        "tariff": context.user_data["rate"],
        "payment_date": datetime.datetime.now()
    }
    response = call_api_post('api/clients/add/', payload=payload)
    update.message.reply_text(
        text='Вы успешно зарегестрированы, можете начать пользоваться нашей платформой. Напишите /start')


def check_frilancer(update, context):
    given_callback = update.callback_query
    if given_callback:
        telegram_id = context.user_data["telegram_id"]
        given_callback.answer()
        given_callback.delete_message()
    else:
        telegram_id = update.message.from_user.id
        context.user_data["telegram_id"] = telegram_id

    chat_id = update.effective_message.chat_id
    endpoint = f"api/freelancers/{chat_id}"
    try:
        response = call_api_get(endpoint)
    except requests.exceptions.HTTPError:
        message_keyboard = [
            ['Пройти верификацию']
        ]
        markup = ReplyKeyboardMarkup(
            message_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
        update.message.reply_text(
            text='Что-бы принимать заказы вам нужно сначала пройти верификацию, '
                 'нажмите кнопку "Пройти верификацию"', reply_markup=markup
        )
        return States.VERIFICATE
    message_keyboard = [
        ['Выбрать заказ', 'Мои заказы']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(
        text='Выберете следующее действие:', reply_markup=markup
    )
    return States.FRILANCER


def verify_freelancer(update, context):
    chat_id = update.effective_message.chat_id
    endpoint = "api/freelancers/add"
    payload = {
        "chat_id": chat_id,
    }
    call_api_post(endpoint, payload)
    message_keyboard = [["Клиент", "Исполнитель"],
                        ['Написать администратору']]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(
        text='Поздравляем, вы прошли верификацию, теперь вы можете брать '
             'заказы.', reply_markup=markup
    )
    return States.START


def check(update, context):
    order_id = update.message.text.replace('/order_', '')
    context.user_data['order_id'] = order_id
    endpoint = f'api/order/{order_id}'
    order = call_api_get(endpoint)
    context.user_data['client_chat_id'] = order['client']['chat_id']
    context.user_data['order_title'] = order["title"]
    context.user_data['dialogue'] = order["dialogue"]
    message = f'Название заказа - {order["title"]}\n\nОписание: ' \
              f'{order["description"]}'
    if order['freelancer'] is None:
        message_keyboard = [
            [f'Взять в работу заказ №{order_id}'],
            ['Назад']
        ]
        markup = ReplyKeyboardMarkup(
            message_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
        update.message.reply_text(text=message, reply_markup=markup)
        for file in order['files']:
            document_name = file.partition('/')[2]
            with open(file, 'rb') as file:
                document = file.read()
            update.message.reply_document(
                document,
                filename=document_name)
        return States.FRILANCER_ORDERS
    else:
        message_keyboard = [
            [f'Подтвердить выполнение заказа №{order_id}'],
            ['Посмотреть переписку'],
            ['Назад']
        ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=message, reply_markup=markup)
    for file in order['files']:
        document_name = file.partition('/')[2]
        with open(file, 'rb') as file:
            document = file.read()
        update.message.reply_document(
            document,
            filename=document_name)
    return States.ORDERS


def send_frilancer_dialogue(update, context):
    order_title = context.user_data['order_title']
    order_id = context.user_data['order_id']
    dialogue_list = context.user_data['dialogue']
    dialogue = ' '.join(dialogue_list)
    message = dedent(f"""\
                           <b>Название заказа</b>
                           {order_title}
                           <b>Переписка:</b>
                           {dialogue}
                          """).replace("    ", "")

    message_keyboard = [
            [f'Подтвердить выполнение заказа №{order_id}'],
            ['Посмотреть переписку'],
            ['Назад']
        ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=message,
                              reply_markup=markup,
                              parse_mode=ParseMode.HTML)
    return States.ORDERS


def finish_orders(update, context):
    order_id = update.message.text.replace('Подтвердить выполнение заказа №', '')
    endpoint = f'api/order/finish'
    payload = {
        "order_id": order_id,
    }
    call_api_post(endpoint, payload)
    message_keyboard = [
        ['Показать все заказы в работе', 'Назад'],
        ['Главное меню']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(
        text="Заказ помечен как выполненный", reply_markup=markup
    )
    return States.FRILANCER_ORDERS


def add_orders_to_frilancer(update, context):
    chat_id = update.effective_message.chat_id
    order_id = update.message.text.replace('Взять в работу заказ №', '')
    endpoint = f'api/order/{order_id}'
    order = call_api_get(endpoint)
    context.user_data['client_chat_id'] = order['client']['chat_id']
    endpoint = f'api/freelancers/appoint'
    payload = {
        "order_id": order_id,
        "chat_id": chat_id
    }
    call_api_post(endpoint, payload)
    message_keyboard = [
        ['Показать все заказы в работе', 'Назад'],
        ['Главное меню']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text="Заказ взят в работу. Напишите клиенту об этом", reply_markup=markup)
    return States.FRILANCER_ORDERS


def send_message_to_client(update, context):
    message_from_frilanser = update.message.text
    user_fullname = str(update.message.from_user['first_name']) + ' ' + str(update.message.from_user['last_name'])
    order_id = context.user_data['order_id']
    order_title = context.user_data['order_title']
    message_to_client = dedent(f"""\
                    <b>Сообщение от {user_fullname}</b>

                    <b>Текст сообщение:</b>
                    {message_from_frilanser}

                    <b>Нажми кнопку "Ответить"</b>
                    """).replace("    ", "")
    endpoint = f'api/contact/'
    payload = {
        "order_id": int(order_id),
        "message": f'{user_fullname}: {message_from_frilanser}',
    }
    call_api_post(endpoint, payload)

    update.message.chat.id = context.user_data['client_chat_id']
    message_keyboard = [
        [f'Ответить исполнителю/{context.user_data["telegram_id"]} - заказ №{order_id}']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True)

    update.message.reply_text(text=message_to_client,
                                reply_markup=markup,
                                parse_mode=ParseMode.HTML)

    update.message.chat.id = context.user_data["telegram_id"]
    message_keyboard = [
        ['Вернуться к заказам']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='сообщение отправлено',
                              reply_markup=markup)
    return States.ORDERS


def handle_message_from_frilanser(update, context):
    message_from_button = update.message.text
    order_id = message_from_button.partition('№')[2]
    context.user_data['frilanser_order_id'] = order_id
    chat_id = message_from_button.replace('Ответить исполнителю/', '')
    chat_id = chat_id.partition(' ')[0]
    context.user_data['frilanser_chat_id'] = chat_id
    update.message.reply_text(text='Напиши ответ исполнителю')
    return States.ANSWER_TO_FRILANSER


def send_message_to_frilanser(update, context):
    message_to_frilanser = update.message.text
    user_fullname = str(update.message.from_user['first_name']) + ' ' + str(update.message.from_user['last_name'])
    order_id = context.user_data['frilanser_order_id']

    message_to_frilancer = dedent(f"""\
                    <b>Сообщение от {user_fullname}</b>

                    <b>Текст сообщение:</b>
                    {message_to_frilanser}
                    """).replace("    ", "")
    endpoint = f'api/contact/'
    payload = {
        "order_id": int(order_id),
        "message": f'{user_fullname}: {message_to_frilanser}',
    }
    call_api_post(endpoint, payload)

    update.message.chat.id = context.user_data['frilanser_chat_id']
    update.message.reply_text(text=message_to_frilancer,
                              parse_mode=ParseMode.HTML)

    update.message.chat.id = context.user_data["telegram_id"]
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='сообщение отправлено',
                              reply_markup=markup)
    return States.ANSWER_TO_FRILANSER


def send_new_order(update, context):
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(
        text='Укажите короткое имя заказа, чтобы потом его легче было искать',
        reply_markup=markup
    )
    return States.ORDER_NAME


def create_order_name(update, context):
    context.user_data['order_name'] = update.message.text
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(
        text='Опишите суть заказа', reply_markup=markup
    )
    return States.ORDER_DESCRIPTION


def create_order_description(update, context):
    context.user_data['order_description'] = update.message.text
    message_keyboard = [
        ['Назад', 'Пропустить']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='Прикрепите файлы, если нужно (при отправки файла в ТГ уберите галочку сжатие)',
                              reply_markup=markup)
    return States.ORDER_FILES


def add_file_to_order(update, context):
    telegram_id = context.user_data["telegram_id"]
    order_name = context.user_data['order_name']
    if not os.path.exists(f'media/{telegram_id}/{order_name}'):
        if not os.path.exists('media'):
            os.mkdir('media')
            os.mkdir(f'media/{telegram_id}')
            os.mkdir(f'media/{telegram_id}/{order_name}')
        else:
            if not os.path.exists(f'media/{telegram_id}'):
                os.mkdir(f'media/{telegram_id}')
                os.mkdir(f'media/{telegram_id}/{order_name}')
            else:
                os.mkdir(f'media/{telegram_id}/{order_name}')
    document_name = update.message.document.file_name
    document = update.message.document.get_file()
    document.download(f'media/{telegram_id}/{order_name}/{document_name}')

    message_keyboard = [
        ['Пропустить']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    message = 'Вы прикрепили файл к заказу, если нужно добавить еще файлы - ' \
              'добавляйте, либо нажмите "Пропустить" для формирования и ' \
              'отправки заказа'
    update.message.reply_text(text=message, reply_markup=markup)
    return States.ORDER_FILES


def create_order(update, context):
    order_name = context.user_data['order_name']
    order_description = context.user_data['order_description']
    telegram_id = context.user_data["telegram_id"]
    if os.path.exists(f'media/{telegram_id}/{order_name}'):
        order_files = []
        files_name = os.listdir(f'media/{telegram_id}/{order_name}')
        for name in files_name:
            order_files.append(f'media/{telegram_id}/{order_name}/{name}')
    else:
        order_files = []
    payload = {
        'title': order_name,
        'description': order_description,
        'chat_id': telegram_id,
        'files': order_files
    }
    call_api_post("api/order/add", payload)

    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    message = dedent("""\
        Вы успешно создали заказ. Ожидайте, в ближайшее время с вами свяжется исполнитель ✌️

        А пока я вам спою "ля-ля-ля, духаст мищь"
        Если вам понравилась песня, можете задонатить по номеру телефона +79805677474.

        А если нет, то нажмите "Назад"
        """).replace("  ", "")
    update.message.reply_text(text=message, reply_markup=markup)
    return States.ORDER_FILES


def show_orders(update, context):
    chat_id = context.user_data["telegram_id"]
    url = f'api/clients/{chat_id}/orders'
    orders = call_api_get(url)
    ps = [
        f'/order_{p["id"]}⬅РЕДАКТИРОВАТЬ ЗАКАЗ. \n {p["title"]} \n\n' for count, p in enumerate(orders)]
    messages = ' '.join(ps)
    message_keyboard = [
        ['Назад', 'Главное меню']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=messages, reply_markup=markup)
    return States.CLIENT_ORDERS


def check_client_order(update, context):
    order_id = update.message.text.replace('/order_', '')
    context.user_data['order_id'] = order_id
    endpoint = f'api/order/{order_id}'
    order = call_api_get(endpoint)
    context.user_data['order_title'] = order["title"]
    context.user_data['dialogue'] = order["dialogue"]
    message = f'Название заказа - {order["title"]}\n\nОписание: {order["description"]}'
    message_keyboard = [
        ['Посмотреть переписку'],
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=message, reply_markup=markup)
    for file in order['files']:
        document_name = file.partition('/')[2]
        with open(file, 'rb') as file:
            document = file.read()
        update.message.reply_document(
            document,
            filename=document_name)

    return States.CLIENT_ORDERS


def send_client_dialogue(update, context):
    order_title = context.user_data['order_title']
    order_id = context.user_data['order_id']
    dialogue_list = context.user_data['dialogue']
    dialogue = ' '.join(dialogue_list)
    message = dedent(f"""\
                           <b>Название заказа</b>
                           {order_title}
                           <b>Переписка:</b>
                           {dialogue}
                          """).replace("    ", "")

    message_keyboard = [
        ['Назад']
        ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=message,
                              reply_markup=markup,
                              parse_mode=ParseMode.HTML)
    return States.CLIENT_ORDERS


def show_five_orders(update, context):
    text = update.message.text
    if context.user_data['five_orders'] == '':
        context.user_data['five_orders'] = call_api_get(f'api/order/find')
    else:
        if text == 'Следующие заказы':
            context.user_data['count'] += 1
            context.user_data['five_orders'] = call_api_get(
                f'api/order/find?page={context.user_data["count"]}'
            )
        elif text == 'Предыдущие заказы':
            context.user_data['count'] -= 1
            context.user_data['five_orders'] = call_api_get(
                f'api/order/find?page={context.user_data["count"]}'
            )
    orders_response = [
        f'/order_{order["id"]}⬅ВЫБРАТЬ ЗАКАЗ. \n {order["title"]} \n\n'
        for order in context.user_data["five_orders"]["results"]
    ]
    messages = ' '.join(orders_response)
    if not context.user_data['five_orders']['previous'] and \
            not context.user_data['five_orders']['next']:
        message_keyboard = [
            ['Назад']
        ]
    elif context.user_data['five_orders']['previous'] and \
            context.user_data['five_orders']['next']:
        message_keyboard = [
            ['Предыдущие заказы', 'Следующие заказы'],
            ['Назад']
        ]
    elif context.user_data['five_orders']['previous'] and \
            not context.user_data['five_orders']['next']:
        message_keyboard = [
            ['Предыдущие заказы'],
            ['Назад']
        ]
    elif not context.user_data['five_orders']['previous'] and \
            context.user_data['five_orders']['next']:
        message_keyboard = [
            ['Следующие заказы'],
            ['Назад']
        ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=messages, reply_markup=markup)
    return States.ORDERS_PAGINATOR


def show_frilancer_orders(update, context):
    chat_id = update.effective_message.chat_id
    url = f'api/freelancers/{chat_id}/orders'
    orders = call_api_get(url)
    if not orders:
        messages = 'У вас пока нет заказов в работе.'
    else:
        orders_response = [
            f'/order_{order["id"]}⬅РЕДАКТИРОВАТЬ ЗАКАЗ. \n {order["title"]} \n\n'
            for order in orders
        ]
        messages = ' '.join(orders_response)
    message_keyboard = [
        ['Назад', 'Главное меню']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=messages, reply_markup=markup)
    return States.FRILANCER_ORDERS


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    env = environs.Env()
    env.read_env()

    telegram_bot_token = env.str("TG_BOT_TOKEN")

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            States.START: [
                MessageHandler(Filters.text("Клиент 😊"), check_client),
                MessageHandler(Filters.text("Исполнитель 🥷"), check_frilancer),
                MessageHandler(Filters.text('Написать администратору ✍️'), message_to_admin),
            ],
            States.ADMIN: [
                MessageHandler(Filters.text, send_to_admin),
            ],
            States.VERIFICATE: [
                MessageHandler(Filters.text('Пройти верификацию'), verify_freelancer),
                MessageHandler(Filters.text, start),
            ],
            States.FRILANCER: [
                MessageHandler(Filters.command(False), check),
                CommandHandler('order', check),
                MessageHandler(Filters.text('Выбрать заказ'), show_five_orders),
                MessageHandler(Filters.text('Мои заказы'), show_frilancer_orders),
                MessageHandler(Filters.text('Следующие заказы'), show_five_orders),
                MessageHandler(Filters.text('Взять в работу'), add_orders_to_frilancer),
                MessageHandler(Filters.text('Назад'), show_five_orders),

                MessageHandler(Filters.text, start),
            ],
            States.FRILANCER_ORDERS: [
                MessageHandler(Filters.command(False), check),
                CommandHandler('order', check),
                MessageHandler(Filters.text('Назад'), show_five_orders),
                MessageHandler(Filters.text('Показать все заказы в работе'), show_frilancer_orders),
                MessageHandler(Filters.text('Главное меню'), start),
                MessageHandler(Filters.text('Вернуться к заказам'), show_five_orders),
                MessageHandler(check_do_to_work, add_orders_to_frilancer),
                MessageHandler(Filters.text, send_message_to_client),
            ],
            States.ORDERS_PAGINATOR: [
                MessageHandler(Filters.command(False), check),
                CommandHandler('order', check),
                MessageHandler(Filters.text('Назад'), start),
                MessageHandler(Filters.text('Предыдущие заказы'), show_five_orders),
                MessageHandler(Filters.text('Следующие заказы'), show_five_orders),
                MessageHandler(Filters.text, start),
            ],
            States.PRICE: [
                MessageHandler(Filters.text("Назад"), start),
                MessageHandler(check_answer, handle_message_from_frilanser),
                MessageHandler(Filters.text, chooze_rate),
            ],
            States.ORDERS: [
                MessageHandler(Filters.text("Новый заказ"), send_new_order),
                MessageHandler(Filters.text("Мои заказы"), show_orders),
                MessageHandler(Filters.text('Назад'), show_frilancer_orders),
                MessageHandler(Filters.text('Главное меню'), start),
                MessageHandler(Filters.text('Вернуться к заказам'), show_five_orders),
                MessageHandler(Filters.text('Посмотреть переписку'), send_frilancer_dialogue),
                MessageHandler(check_do_to_work, finish_orders),
                MessageHandler(check_answer, handle_message_from_frilanser),
                MessageHandler(Filters.text, send_message_to_client),
            ],
            States.ORDER_NAME: [
                MessageHandler(Filters.text("Назад"), send_new_order),
                MessageHandler(check_answer, handle_message_from_frilanser),
                MessageHandler(Filters.text, create_order_name),
            ],
            States.ORDER_DESCRIPTION: [
                MessageHandler(Filters.text("Назад"), check_client),
                MessageHandler(check_answer, handle_message_from_frilanser),
                MessageHandler(Filters.text, create_order_description),
            ],
            States.ORDER_FILES: [
                MessageHandler(Filters.text('Пропустить'), create_order),
                MessageHandler(Filters.text("Назад"), check_client),
                MessageHandler(Filters.document, add_file_to_order),
                MessageHandler(check_answer, handle_message_from_frilanser),
            ],
            States.CLIENT_ORDERS: [
                MessageHandler(Filters.command(False), check_client_order),
                CommandHandler('order', check_client_order),
                MessageHandler(Filters.text('Назад'), check_client),
                MessageHandler(Filters.text('Главное меню'), start),
                MessageHandler(Filters.text('Посмотреть переписку'), send_client_dialogue),
                MessageHandler(check_answer, handle_message_from_frilanser),

            ],
            States.RATE_CHOIСE: [
                MessageHandler(Filters.text("Выбрать"), send_payment),
                MessageHandler(Filters.text("Назад"), check_client),
                MessageHandler(check_answer, handle_message_from_frilanser),
            ],
            States.PAYMENT: [
                MessageHandler(Filters.text("Оплатить"), add_user),
                MessageHandler(Filters.text("Назад"), check_client),
                MessageHandler(check_answer, handle_message_from_frilanser),
            ],
            States.ANSWER_TO_FRILANSER: [
                MessageHandler(Filters.text("Назад"), check_client),
                MessageHandler(check_answer, handle_message_from_frilanser),
                MessageHandler(Filters.text, send_message_to_frilanser),
            ],
        },
        fallbacks=[],
        allow_reentry=True,
        name='bot_conversation',
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

