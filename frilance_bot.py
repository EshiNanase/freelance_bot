import argparse
import logging
import datetime
import random
import requests
from enum import Enum, auto
from textwrap import dedent
from telegram import ParseMode
from more_itertools import chunked
from itertools import cycle

import environs
from telegram import ReplyKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)


logger = logging.getLogger(__name__)


class States(Enum):
    START = auto()
    ADMIN = auto()
    PRICE = auto()
    ORDERS = auto()
    RATE_CHOIСE = auto()
    PAYMENT = auto()
    VERIFICATE = auto()
    FRILANCER = auto()
    FRILANCER_ORDERS = auto()


class BotData:
    ADMIN_CHAT_ID = 704859099


def call_api_get(endpoint):
    url = f"http://127.0.0.1:8000/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def call_api_post(endpoint, payload):
    url = f"http://127.0.0.1:8000/{endpoint}"
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


def start(update, context):
    user = update.effective_user
    greetings = dedent(fr'''
                            Приветствую {user.mention_markdown_v2()}\!
                            Я бот сервисной поддержки для PHP
                            Укажи свой статус\.''')

    message_keyboard = [["Клиент", "Исполнитель"],
                        ['Написать администратору']]

    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_markdown_v2(text=greetings,
                                     reply_markup=markup)
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
                это видит флорист
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

    url = f"http://127.0.0.1:8000/api/clients/{telegram_id}"
    response = requests.get(url)

    # status = 1

    if response.ok:
    # if status == 1:
        rest_days = response.json()['days_left']
        rest_orders = response.json()['requests_left']
        rate_name = response.json()['tariff_title']
        user = update.effective_user
        greetings = dedent(f'''
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

    # message_keyboard = [
    #     ['Эконом', 'Продвинутый'],
    #     ['VIP', 'Назад']
    # ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    with open('documents/Тарифы.pdf', 'rb') as image:
        price_pdf = image.read()

    greeting_msg = dedent("""\
        Привет!✌️

        Вы еще не зарегестрированы на нашем сайте. Для регистрации ознакомьтесь с нашим предложением\
         и выберите подходящий тариф

        Это обязательная процедура, для продолжения пользования сайтом необходимо выбрать и оплатить тариф.
        """).replace("  ", "")
    update.message.reply_document(
        price_pdf,
        filename="Тарифы.pdf",
        caption=greeting_msg,
        reply_markup=markup)

    return States.PRICE


def chooze_rate(update, context):
    context.user_data["rate"] = update.message.text
    url = f"http://127.0.0.1:8000/api/tariff/{update.message.text}"
    response = requests.get(url)
    response.raise_for_status()
    rate_name = response.json()['title']
    rate_description = response.json()['description']
    # rate_description = 'бла бла бла'
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
    # update.message.reply_text(text='тариф выбран',
    #                           reply_markup=markup)
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
    update.message.reply_text(text='здесь информация по оплате и прикручена система оплаты',
                              reply_markup=markup)
    return States.PAYMENT


def add_user(update, context):
    payload = {
        "chat_id": context.user_data["telegram_id"],
        "tariff": context.user_data["rate"],
        "payment_date": datetime.datetime.now()
    }
    response = call_api_post('api/clients/add/', payload=payload)
    update.message.reply_text(text='Вы успешно зарегестрированы, можете начать пользоваться нашей платформой. Напишите /start')


def check_frilancer(update, context):
    chat_id = update.effective_message.chat_id
    print(chat_id)
    url = f"http://127.0.0.1:8000/api/freelancers/{chat_id}"
    response = requests.get(url)
    x = response.status_code
    if response.status_code == 404:
        message_keyboard = [
            ['Пройти верификацию']
        ]
        markup = ReplyKeyboardMarkup(
            message_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
        update.message.reply_text(text='Что-бы принимать заказы вам нужно сначала пройти верификацию, '
                                       'нажмите кнопку "Пройти верификацию"',
                                  reply_markup=markup)
        return States.VERIFICATE
    message_keyboard = [
        ['Выбрать заказ', 'Мои заказы']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='Выберете следующее действие:',
                              reply_markup=markup)

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
    update.message.reply_text(text='Поздравляем, вы прошли верификацию, теперь вы можете брать заказы.',
                              reply_markup=markup)
    return States.START


def check(update, context):

    order_id = update.message.text.replace('/order_', '')
    endpoint = f'api/order/{order_id}'
    order = call_api_get(endpoint)
    message = f'Название заказа - {order["title"]}\n\nОписание: {order["description"]}'
    if order['freelancer'] is None:
        message_keyboard = [
            [f'Взять в работу заказ №{order_id}'],
            ['Назад']
        ]
    else:
        message_keyboard = [
            [f'Подтвердить выполнение заказа №{order_id}'],
            ['Получить контакт заказчика'],
            ['Назад']
        ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=message, reply_markup=markup)
    return States.FRILANCER_ORDERS


def add_orders_to_frilancer(update, context):
    chat_id = update.effective_message.chat_id
    order_id = update.message.text.replace('Взять в работу заказ №', '')
    print(order_id)
    endpoint = f'api/order/{order_id}'
    order = call_api_get(endpoint)

    endpoint = f'api/freelancers/appoint'
    payload = {
        "order_id": order_id,
        "chat_id": chat_id
    }
    call_api_post(endpoint, payload)
    message_keyboard = [
        ['Взять в работу'],
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text="Заказ взят в работу", reply_markup=markup)
    return States.FRILANCER_ORDERS


def send_new_order(update, context):
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='Заказ', reply_markup=markup)
    return States.PRICE


def show_orders(update, context):
    orders = call_api_get('api/all_orders')
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='Мои заказы', reply_markup=markup)
    return States.PRICE


def func_chunks_generators(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


five = ''
orders_by_five_elements = ''
def show_five_orders(update, context):
    global five
    global orders_by_five_elements
    if five == '':
        endpoint = 'api/all_orders'
        orders = call_api_get(endpoint)
        orders_title = [order for order in orders]
        orders_by_five_elements = cycle(func_chunks_generators(orders_title, 5))
        five = next(orders_by_five_elements)
    else:
        five = next(orders_by_five_elements)

    ps = [
        f'/order_{p["id"]}⬅ВЫБРАТЬ ЗАКАЗ. \n {p["title"]} \n\n' for count, p in enumerate(five)]
    messages = ' '.join(ps)
    message_keyboard = [
        ['Назад', 'Следующие заказы']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text=messages, reply_markup=markup)
    return States.FRILANCER


def show_frilancer_orders(update, context):
    chat_id = update.effective_message.chat_id
    url = f'api/freelancers/{chat_id}/orders'
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
    return States.FRILANCER_ORDERS


# def error(update, context):
#     logger.warning('Update "%s" caused error "%s"', update, error)
#     update.message.reply_text('Произошла ошибка')


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
                MessageHandler(Filters.text("Клиент"), check_client),
                MessageHandler(Filters.text("Исполнитель"), check_frilancer),
                MessageHandler(Filters.text('Написать администратору'), message_to_admin),
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

                MessageHandler(Filters.text, start),
            ],
            States.FRILANCER_ORDERS: [
                MessageHandler(Filters.command(False), check),
                CommandHandler('order', check),
                MessageHandler(Filters.text('Назад'), show_five_orders),
                MessageHandler(Filters.text('Взять в работу'), show_frilancer_orders),
                MessageHandler(Filters.text('Главное меню'), start),
                MessageHandler(Filters.text, add_orders_to_frilancer),
            ],
            States.PRICE: [
                MessageHandler(Filters.text("Назад"), start),
                MessageHandler(Filters.text, chooze_rate),
            ],
            States.ORDERS: [
                MessageHandler(Filters.text("Новый заказ"), send_new_order),
                MessageHandler(Filters.text("Мои заказы"), show_orders),
            ],
            States.RATE_CHOIСE: [
                MessageHandler(Filters.text("Выбрать"), send_payment),
                MessageHandler(Filters.text("Назад"), check_client),
            ],
            States.PAYMENT: [
                MessageHandler(Filters.text("Оплатить"), add_user),
                MessageHandler(Filters.text("Назад"), check_client),
            ],
        },
        fallbacks=[],
        allow_reentry=True,
        name='bot_conversation',
    )

    dispatcher.add_handler(conv_handler)
    # dispatcher.add_error_handler(error)
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()