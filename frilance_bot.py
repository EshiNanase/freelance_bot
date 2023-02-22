import argparse
import logging
import datetime
import random
import requests
from enum import Enum, auto
from textwrap import dedent
from telegram import ParseMode
from more_itertools import chunked

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
        rest_days = response.json()['rest_days']
        rest_orders = response.json()['rest_orders']
        rate_name = response.json()['rate_name']

        user = update.effective_user
        greetings = dedent(fr'''
                        {user.mention_markdown_v2()}\!
                        Ваш тариф "{rate_name}"
                        Тариф действует до {rest_days}
                        В вашем тарифе осталось {rest_orders} запросов\.''')
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

        update.message.reply_markdown_v2(text=greetings, reply_markup=markup)
        return States.ORDERS

    response = call_api_get('api/all_tariffs/')
    rates = response['tariffs']
    rates.extend(["Назад"])
    message_keyboard = list(chunked(rates, 2))

    # message_keyboard = [
    #     ['Базовый', 'Продвинутый'],
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
    # rate_description = response.json()['description']
    rate_description = 'бла бла бла'
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
        "user_tg_id": context.user_data["user_telegram_id"],
        "rate": context.user_data["rate"],
        "payment_date": datetime.datetime.now()
    }
    response = call_api_post('api/clients/add/', payload=payload)
    if response.ok:
        update.message.reply_text(text='Вы успешно зарегестрированы, можете начать пользоваться нашей платформой. Напишите /start')


def check_frilancer(update, context):
    message_keyboard = [
        ['Назад']
    ]
    markup = ReplyKeyboardMarkup(
        message_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    update.message.reply_text(text='Фрилансер', reply_markup=markup)
    return States.PRICE


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