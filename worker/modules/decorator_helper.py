from logger import logger
from modules import context_helper
from modules import fsm


def catch_possible_spam(func):
    def wrapper(update, context):
        if context_helper.is_possible_spam(update, context):
            if context_helper.required_to_send_do_not_spam(update, context):
                fsm.States.run_do_not_spam_state(update, context)
            return

        context.user_data.write('sent_do_not_spam_time', None)
        return func(update, context)

    return wrapper


def session_handler(func):
    def wrapper(update, context):
        if context_helper.is_session_expired(update, context):
            logger.info('in session_handler curr {}'.format(context.user_data.get('current_state')))
            logger.info('in session_handler next {}'.format(context.user_data.get('next_state')))

            if context.user_data.get('next_state') in fsm.States.session_expired_ignore_states:
                current_state = context.user_data.get('current_state')
                next_state = context.user_data.get('next_state')
                logger.info(f'in session_handler is ignored: {next_state}')

                fsm.States.init_state(update, context)

                context.user_data.write('current_state', current_state)
                context.user_data.write('next_state', next_state)

                return func(update, context)

            fsm.States.init_state(update, context)
            fsm.States.states_map['SESSION_EXPIRED'].run_state(update, context)
            context.user_data.write('next_state', 'SESSION_EXPIRED')
            fsm.transition_next_state(update, context)
            return

        return func(update, context)

    return wrapper


def pending_reply_handler(func):
    def wrapper(update, context):
        if context_helper.is_pending_reply(update, context):
            return func(update, context)

        fsm.States.run_default_error_state(update, context)

    return wrapper
