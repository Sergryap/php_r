import os
import time
import textwrap
import telegram.ext
import phonenumbers


from telegram.ext import (
    Updater,
    Filters,
    CallbackQueryHandler,
    PollAnswerHandler,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    )

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from users.models import User, Freelancer, Customer
from service.tg_lib import (
    show_auth_keyboard,
    show_send_contact_keyboard,
    show_auth_user_type,
    show_freelancer_start,
    show_customer_start
)
from pprint import pprint


def get_user(func):
    def wrapper(update, context):
        chat_id = update.effective_chat.id
        user, _ = User.objects.get_or_create(telegram_id=chat_id)
        context.user_data['user'] = user
        return func(update, context)
    return wrapper


class TgDialogBot:

    def __init__(self, tg_token, states_functions):
        self.tg_token = tg_token
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token, use_context=True)
        self.updater.dispatcher.add_handler(CommandHandler('start', get_user(self.handle_users_reply)))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(get_user(self.handle_users_reply)))
        self.updater.dispatcher.add_handler(
            MessageHandler(Filters.text | Filters.contact, get_user(self.handle_users_reply))
        )

    def handle_users_reply(self, update, context):
        user = context.user_data['user']
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        elif update.poll_answer:
            user_reply = update.poll_answer.option_ids
            chat_id = update.poll_answer.user.id
        else:
            return

        if user_reply == '/start':
            user_state = 'START'
            context.user_data.update({'chat_id': chat_id, 'full_name': '', 'phone_number': ''})
        else:
            user_state = user.bot_state
            user_state = user_state if user_state else 'HANDLE_AUTH'

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        user.bot_state = next_state
        user.save()


def start(update, context):
    chat_id = update.message.chat_id
    show_auth_keyboard(context, chat_id)
    return 'HANDLE_AUTH'


def handle_auth(update, context):
    user = context.user_data['user']
    chat_id = update.effective_chat.id
    if update.callback_query:
        user_data = context.user_data
        ############# Данные для записи в БД ###############
        name_data = user_data['full_name'].split()
        name = user_data['full_name'].split()[0].strip()
        surname = user_data['full_name'].split()[1].strip() if len(name_data) > 1 else ''
        phone_number = user_data['phone_number']
        ####################################################
        user.phone_number = phone_number
        user.first_name = name
        user.last_name = surname
        user.save()
        status = update.callback_query.data
        print(status)
        pprint(user_data)
        if status == 'Freelancer':

            context.user_data['status'] = 'Freelancer'
            show_freelancer_start(context, chat_id)
            pprint(context.user_data)
            return 'HANDLE_FREELANCER'
        elif status == 'Customer':
            context.user_data['status'] = 'Customer'
            show_customer_start(context, chat_id)
            return 'HANDLE_CUSTOMER'
    if not update.message:
        return 'HANDLE_AUTH'
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        if phone_number and phonenumbers.is_valid_number(phonenumbers.parse(phone_number, 'RU')):
            context.user_data['phone_number'] = phone_number
            context.bot.send_message(
                chat_id=chat_id,
                text=f'Введите Ваше Имя и Фамилию:',
                reply_markup=telegram.ReplyKeyboardRemove()
                )
            return 'HANDLE_AUTH'
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Вы ввели неверный номер телефона. Попробуйте еще раз:'
                )
            return 'HANDLE_AUTH'
    elif update.message.text:
        if 'Авторизоваться' in update.message.text:
            show_send_contact_keyboard(context, chat_id)
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            return 'HANDLE_AUTH'
        else:
            show_auth_user_type(context, chat_id)
            context.user_data['full_name'] = update.message.text
            return 'HANDLE_AUTH'


def handle_customer(update, context):
    if update.callback_query and update.callback_query.data in ['economic', 'standard', 'vip']:
        user_reply = update.callback_query.data
        value = {'economic': 500, 'standard': 1000, 'vip': 3000}
        total_value = value[user_reply]
        context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title='Оплата заказа в pizza-store',
            description='Payment Example using python-telegram-bot',
            payload='Custom-Payload',
            provider_token=os.environ['PROVIDER_TOKEN'],
            currency='RUB',
            prices=[LabeledPrice('Test', total_value * 100)]
        )
        return 'PRECHECKOUT'


def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        context.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message="Something went wrong...")
    else:
        context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    # context.bot.send_message(
    #     chat_id=update.effective_user.id,
    #     text='Хотите продолжить?',
    #     reply_markup=btn.get_restart_button()
    # )
    return 'HANDLE_CUSTOMER'
