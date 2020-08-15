from logger import logger
from modules.context_helper import set_pending_reply
from modules import fsm
from modules.decorator_helper import catch_possible_spam, session_handler, pending_reply_handler


@catch_possible_spam
@pending_reply_handler
@session_handler
def process_text(update, context):
    prev_state = fsm.States.get_prev_state(update, context)
    current_state = fsm.States.get_current_state(update, context)
    context.user_data.write('sent_do_not_spam_time', None)

    logger.info('Callback: process_text')
    logger.info(f'{prev_state.state}, {current_state.state}')

    if current_state is not None:
        set_pending_reply(update, context, False)
        fsm.transition_next_state(update, context)
        return

    fsm.States.run_default_error_state(update, context)
    set_pending_reply(update, context, True)
