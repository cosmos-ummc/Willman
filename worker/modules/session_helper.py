from modules.context_helper import get_current_context
from modules.strings import Strings

from message import message_handler


def session_expired_message(update, context):
    chat_id, message = get_current_context(update, context)
    message_handler.send_to_pool({
        'chat_id': chat_id,
        'text': Strings.get_string("MISC_SESSION_EXPIRED", update, context)
    })
