from logger import logger
from modules import strings
from modules.context_helper import get_current_context
from message import message_handler


class UnknownError(Exception):
    pass


class TryAgainError(Exception):
    pass


def telegram_error(update, context):
    """Log Errors caused by Updates."""
    chat_id, message = get_current_context(update, context)
    logger.exception(context.error)
    message_handler.send_to_pool({
        'chat_id': chat_id,
        'text': strings.Strings.get_string("ERROR_OCCURRED", update, context)
    })
