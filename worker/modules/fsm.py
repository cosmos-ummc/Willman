import yaml

from logger import logger
from modules.context_helper import set_pending_reply
from modules.error_helper import UnknownError, TryAgainError
from modules.fsm_states.states import _States, State


def transition_next_state(update, context):
    # get current and next states
    # current is next state of previous state
    prev_state = States.get_prev_state(update, context)  # type: State
    current_state = States.get_current_state(update, context)  # type: State

    # check if it is a question state
    if current_state is not None and current_state.state_type == 'question':
        try:
            # if yes, store answer
            current_state.run_save_param(update, context)
        except TryAgainError:
            # if answer is not correct
            current_state.run_error_state(update, context)
            set_pending_reply(update, context, True)
            return False

    def print_if_not_none(prefix, state):
        if state is not None:
            logger.info(f'{prefix} {state.state}')
        else:
            logger.info(f'{prefix} {None}')

    print_if_not_none('prev', prev_state)
    print_if_not_none('curr', current_state)

    try:
        # if state_type == 'action', get_next_state will perform_action and determine what is its next state
        # e.g. if_else will choose 0 or 1 depending on if else results
        next_state = current_state.get_next_state(update, context)
    except UnknownError as e:  # this is usually due to server error
        # if perform_action raise error, catch here
        logger.exception(e)
        if current_state.has_error_state():  # check if user has defined error state
            current_state.run_error_state(update, context)
        else:
            current_state.run_server_error_state(update, context)  # send server error

        set_pending_reply(update, context, True)
        return False

    # if no more next state, indicating the flow has ended, return True
    if next_state is None:
        if prev_state is not None:
            logger.info(f'Ended curr state {current_state.state} from: {prev_state.state}')
        else:
            logger.info(f'Ended curr state {current_state.state}')
        return True

    # run_state here is to send message (and "action" will have no effect)
    next_state.run_state(update, context)
    print_if_not_none('next', next_state)

    context.user_data.write('current_state', current_state.state)
    context.user_data.write('next_state', next_state.state)
    set_pending_reply(update, context, next_state.state_type == 'question')

    # if it is not a question state, then just go to next state
    if next_state.state_type in ['command', 'action', 'message']:
        return transition_next_state(update, context)

    return True


def init_states(fn='res/cosmos.yaml'):
    global States
    logger.info('Initialize States')
    f = open(fn, 'r', encoding='utf8')
    fsm_structure = yaml.load(f, yaml.FullLoader)
    States = _States(fsm_structure)


States = None  # type: _States
