import re
import json
import textwrap

import telegram.ext

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from django.utils.timezone import now
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from django.conf import settings
from users.models import Customer, Freelancer
from service.models import Order
from django.db.models import Q


def show_auth_user_type(context, chat_id):
    message = 'Перед началом использования представьтесь кем вы являетесь'
    context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton('Заказчик', callback_data='Customer'),
                    InlineKeyboardButton('Фрилансер', callback_data='Freelancer')
                ]
            ],
            resize_keyboard=True
        )
    )


def show_auth_keyboard(context, chat_id):
    message = textwrap.dedent('''
        Перед началом использования необходимо отправить номер телефона.
        Пожалуйста, нажмите на кнопку Авторизоваться ниже:''')
    auth_keyboard = KeyboardButton(text="🔐 Авторизоваться")
    reply_markup = ReplyKeyboardMarkup(
        [[auth_keyboard]], one_time_keyboard=False,
        row_width=1, resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_send_contact_keyboard(context, chat_id):
    message = '''Продолжая регистрацию вы соглашаетесь с политикой конфиденциальности'''
    contact_keyboard = KeyboardButton(text="☎ Передать контакт", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        [[contact_keyboard]], one_time_keyboard=False,
        row_width=1, resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_freelancer_orders(context, chat_id, freelancer_orders=False):
    if freelancer_orders:
        message = 'Заказы, в которых вы участвуете:'
    else:
        message = 'Выберите заказ для детального ознакомления и при желании выберите его для выполнения:'
    if freelancer_orders:
        orders = Order.objects.filter(freelancer__telegram_id=chat_id)
    else:
        orders = Order.objects.filter(Q(status='33') | Q(status='1 not processed'))
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton('Вернуться назад', callback_data='break')]] + [
            [InlineKeyboardButton(order.title, callback_data=f'detail:{order.pk}')] for order in orders
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_order_detail(context, chat_id, order_pk, button=True):
    order = Order.objects.get(pk=order_pk)
    message = textwrap.dedent(
        f'''
        Название: {order.title}
        Описание: {order.description}
        Создан: {order.created_at}
        '''
    )
    if button:
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton('Вернуться назад', callback_data='break')],
                [InlineKeyboardButton('Выбрать для себя', callback_data=f'choice:{order_pk}')]
            ],
            resize_keyboard=True
        )
    else:
        reply_markup = None
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_freelancer_menu(context, chat_id):
    message = 'Выберите дальнейшее действие:'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton('Доступные заказы', callback_data='free_orders')],
            [InlineKeyboardButton('Посмотреть свои заказы', callback_data='my_orders')],
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_customer_start(context, chat_id):
    message = 'Выберите либо уточните тариф:'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Эконом - 500 р.', callback_data='economy'),
                InlineKeyboardButton('Стандарт - 1000 р.', callback_data='base'),
                InlineKeyboardButton('VIP - 3000 р.', callback_data='vip'),
            ]
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_creating_order_step(context, chat_id, step):
    message = {
        1: 'Введите краткое название заказа',
        2: 'Введите подробное описание заказа',
        3: 'Нажмите чтобы посмотреть весь заказа'
    }
    callback_data = {
        1: 'title',
        2: 'description',
        3: 'verify'
    }
    reply_markup = {
        1: None,
        2: None,
        3: InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton('Весь заказ', callback_data=callback_data[step])]],
            resize_keyboard=True
        ),
    }

    context.bot.send_message(chat_id=chat_id, text=message[step], reply_markup=reply_markup[step])


def show_customer_step(context, chat_id):
    message = 'Выберите дальнейшее действие:'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton('Оплатить тариф', callback_data='pay')],
            [InlineKeyboardButton('Создать заказ', callback_data='create_order')],
            [InlineKeyboardButton('Посмотреть свои заказы', callback_data='show_orders')],
        ],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_customer_orders(update, context):
    user_data = context.user_data
    chat_id = update.effective_chat.id
    customer, _ = Customer.objects.get_or_create(
        username=f'{update.effective_user.username}_{chat_id}',
    )

    orders = Order.objects.filter(client=customer)
    for order in orders:
        status = order.status
        if status == '33' or status == '1 not processed':
            freelancer = 'Не назначен'
            callback_data = 'empty_telegramm_id'
            reply_markup = None
            text = textwrap.dedent(
                f'''
                Название: {order.title},
                Описание: {order.description}
                '''
            )
        else:
            freelancer = f'{order.freelancer.first_name}'
            if customer.status == 'vip':
                text = textwrap.dedent(
                    f'''
                    Название: {order.title},
                    Описание: {order.description},
                    Фрилансер: {freelancer}
                    Телефон фрилансера: {order.freelancer.phone_number}
                    '''
                )
            else:
                text = textwrap.dedent(
                    f'''
                    Название: {order.title},
                    Описание: {order.description},
                    Фрилансер: {freelancer}
                    '''
                )
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            'Написать фрилансеру',
                            callback_data=f"tg_id:{order.freelancer.telegram_id}:{order.pk}"
                        )
                    ]
                ],
                resize_keyboard=True
            )

        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


def show_freelancers(context, chat_id):
    freelancers = Freelancer.objects.all()
    inline_keyboard = [[
            InlineKeyboardButton('Пропустить', callback_data='break')
        ]]
    for freelancer in freelancers:
        inline_keyboard.append([
            InlineKeyboardButton(freelancer.first_name, callback_data=freelancer.telegram_id)
        ])
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
        resize_keyboard=True
    )
    text = 'Выберите исполнителя для подробной информации, либо пропустите'
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


def send_freelancer_message(context, message, freelancer_telegram_id, chat_id):
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton('Ответить заказчику', callback_data=chat_id)]],
        resize_keyboard=True
    )



