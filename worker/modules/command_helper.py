from modules import fsm
from modules.decorator_helper import catch_possible_spam


def generic_command(state_name):
    @catch_possible_spam
    def command(update, context):
        fsm.States.init_state(update, context)

        context.user_data.write('current_state', None)
        context.user_data.write('next_state', state_name)

        fsm.transition_next_state(update, context)

    return command
