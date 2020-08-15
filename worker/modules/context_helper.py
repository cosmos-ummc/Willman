import time
from datetime import datetime
from dateutil import parser

from logger import logger
from modules.constants import Constants


def is_session_expired(update, context, threshold=Constants.SESSION_TIMEOUT):
    prev_time = context.user_data.get('last_sent')
    if prev_time is None:
        prev_time = float(time.time()) * 1000
    else:
        prev_time = float(prev_time)
    curr_time = float(time.time() * 1000)

    context.user_data.write('last_sent', curr_time)
    expired = curr_time - prev_time > threshold
    logger.info(f'is_session_expired = {expired}')
    return expired


def set_last_received(update, context):
    context.user_data.write(f'last_received {float(time.time() * 1000)}')


def is_possible_spam(update, context):
    t1 = int((datetime.utcnow().timestamp() + 0.5))
    t2 = parser.parse(update.date).timestamp()

    time_diff = t1 - t2
    # print(update.message.date)
    # print(update.message.date.timestamp())
    # print(datetime.utcnow())
    # print(datetime.utcnow().timestamp())
    logger.info(f'time_diff = {time_diff}')
    if time_diff > Constants.SESSION_TIMEOUT_SECONDS:
        return True

    min_diff = Constants.MIN_DIFF_IS_SPAM
    prev_time = context.user_data.get('last_received')
    if prev_time is None:
        prev_time = float(time.time() * 1000) - min_diff
    else:
        prev_time = float(prev_time)
    current_time = float(time.time() * 1000)

    # difference between every reply must be at least > min_diff. else the message will be ignored! act as a de-bouncer
    context.user_data.write('last_received', current_time) 
    return current_time - prev_time < min_diff


def required_to_send_do_not_spam(update, context):
    curr_time = int(time.time() * 1000)

    last_sent_time = context.user_data.get('sent_do_not_spam_time', curr_time)
    if last_sent_time:
        last_sent_time = float(last_sent_time)
    context.user_data.write('sent_do_not_spam_time', curr_time)

    if last_sent_time is None or curr_time - last_sent_time >= Constants.MIN_TIME_TO_SEND_DO_NOT_SPAM:
        # bot.send_message(
        #     chat_id,
        #     Strings.get_string("MISC_DO_NOT_SPAM", update, context)
        # )
        return True
    else:
        return False


def is_pending_reply(update, context):
    try:
        pending_reply = context.user_data.get('is_pending_reply', False)
    except AttributeError:
        pending_reply = False

    logger.info(f'is_pending_reply: {pending_reply}')
    return pending_reply


def set_pending_reply(update, context, pending_reply=True):
    context.user_data.write('is_pending_reply', pending_reply)


def get_current_context(update, context):
    try:
        message = update.text
        chat_id = update.chat_id
    except AttributeError:
        # message = update.callback_query.message
        message = update.text
        chat_id = update.chat_id

    return chat_id, message
