import time

from modules import strings
from modules.constants import Constants
from message import message_handler


def bot_send_message(update, context, text, reply_markup=None, remove_keyboard=True):
    time.sleep(Constants.PROMPT_DELAY)

    try:
        chat_id = update.chat_id
    except AttributeError:
        chat_id = update.chat.id

    to_send_msg = strings.Strings.get_string(text['text'], context=context)
    if isinstance(to_send_msg, list):
        to_send_msg = '\n\n'.join(to_send_msg)

    # if context.user_data.get('localization') is None:
    #     to_send_msg = '\n\n'.join(strings.Strings.get_string(text['text'], all_langs=True))
    # else:
    #     to_send_msg = strings.Strings.get_string(text['text'], context=context)

    if text['type'] == 'photo':
        message_handler.send_to_pool({
            'chat_id': chat_id,
            'text': to_send_msg,
            'reply_markup': reply_markup,
            'type': 'photo'
        })

    elif text['type'] == 'document':
        message_handler.send_to_pool({
            'chat_id': chat_id,
            'text': to_send_msg,
            'reply_markup': reply_markup,
            'type': 'photo'
        })
    else:
        if reply_markup is None:
            if not remove_keyboard:
                reply_markup = []
            else:
                reply_markup = [{'text': 'remove', 'type': 'remove'}]

        message_handler.send_to_pool({
            'chat_id': chat_id,
            'text': to_send_msg,
            'reply_markup': reply_markup,
            'type': 'text'
        })


def get_string_from_update(update, context):
    answer = update.text
    return answer


def get_phone_number_from_update(update, context):
    phone_number = update.phone_number
    return phone_number
