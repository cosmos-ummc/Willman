from datetime import datetime
from typing import OrderedDict

from logger import logger
from modules.bot_helper import (
    bot_send_message,
    get_string_from_update,
    get_phone_number_from_update
)
from modules.error_helper import UnknownError, TryAgainError
from modules.fsm_states.action import Action
from modules.fsm_states.command import Command
from modules.fsm_states.keyboards import Keyboards


class _States:
    def __init__(self, yaml_data):
        self.yaml_data = yaml_data

        self.states = yaml_data['states']
        self.commands = yaml_data['commands']

        self.states_map = {}

        self.total_params = []
        self.session_expired_ignore_states = yaml_data['session_expired_ignore_states']

        def _get_param(obj):
            params = []
            for key, val in obj.items():
                if isinstance(val, (dict, OrderedDict)):
                    params += _get_param(val)
                else:
                    params.append(val)
            return params

        for state_data in self.states:
            state = State(self, state_data)
            self.states_map[state.state] = state
            self.total_params.extend(state.params)
            if state.action is not None:
                if isinstance(state.action.params, list):
                    self.total_params.extend(state.action.params)
                else:
                    # self.total_params.extend(state.action.params.values())
                    self.total_params.extend(_get_param(state.action.params))

        total_params = []
        for param in self.total_params:
            if 'INT_' in param:
                param = param.replace('INT_', '')
            elif 'STR_' in param:
                param = param.replace('STR_', '')
            if '_timestamp' in param:
                param = param.replace('_timestamp', '')

            total_params.append(param)

        self.total_params = list(set(total_params))

    def get_prev_state(self, update, context):
        """
        get chat previous state (a.k.a the previous's current state)
        """
        curr_state = context.user_data.get('current_state')
        if curr_state is None:
            return None
        return self.states_map[curr_state]

    def get_current_state(self, update, context):
        """
        get chat current state (a.k.a the previous's next state)
        """
        next_state = context.user_data.get('next_state')
        if next_state is None:
            return None
        return self.states_map[next_state]

    def init_state(self, update, context):
        """
        initialize all states, for all appeared params, initialize as None
        """
        last_received = context.user_data.get('last_received', None)
        pending_reply = context.user_data.get('is_pending_reply', None)
        localization = context.user_data.get('localization', None)
        sent_do_not_spam_time = context.user_data.get('sent_do_not_spam_time', None)
        # message_history = context.user_data.get('message_history', [])
        # patient_type = context.user_data.get('patient_type', None)

        context.user_data.clear()

        context.user_data.write('prev_state', None)
        context.user_data.write('current_state', None)
        context.user_data.write('next_state', None)

        context.user_data.write('is_pending_reply', pending_reply)
        context.user_data.write('last_received', last_received)
        context.user_data.write('sent_do_not_spam_time', sent_do_not_spam_time)
        # context.user_data.write('message_history', message_history)

        for param_key in self.total_params:
            context.user_data.write(param_key, None)

        # if patient_type == RegistrationStatus.COMPLETE:
        context.user_data.write('localization', localization)

    def run_do_not_spam_state(self, update, context):
        error_state = self.states_map['DEFAULT_DO_NOT_SPAM']
        error_texts = error_state.get_texts(update, context)
        for text in error_texts:
            bot_send_message(update, context, text, remove_keyboard=False)

    def run_default_error_state(self, update, context):
        error_state = self.states_map['DEFAULT_ERROR']
        error_texts = error_state.get_texts(update, context)
        for text in error_texts:
            bot_send_message(update, context, text, remove_keyboard=False)

    def run_server_error_state(self, update, context):
        error_state = self.states_map['SERVER_ERROR']
        error_texts = error_state.get_texts(update, context)
        for text in error_texts:
            bot_send_message(update, context, text, remove_keyboard=False)


class State:
    def __init__(self, States: _States, state_data):
        self.States = States
        self.state_data = state_data

        self.state = state_data['state']
        self.state_type = state_data.get('type', 'question')
        self.question_type = state_data.get('question_type', 'choice')

        self.params = state_data.get('params', [])
        self.texts = state_data.get('texts', [])
        self.keyboards = Keyboards(state_data.get('keyboards', []), state_data.get('one_time_keyboard', False))
        self.action = None
        self.command = None
        if self.state_type == 'action':
            self.action = Action(state_data['action'])
        if self.state_type == 'command':
            self.command = Command(state_data['command'])

    def get_texts(self, update, context):
        """
        get all texts ID from self.texts
        the structure is like blow:

        texts:
          - text: text_ID
            type: photo/contact/text
            condition:   # if value of key1 == val1, then send to user
              key1: val1
          - ...
        """
        user_context = context.user_data

        texts = []
        for text_data in self.texts:
            text = text_data['text']
            text_type = text_data.get('type', 'text')
            condition = text_data.get('condition', {})

            if len(condition) != 0:
                for cond_key, cond_val in condition.items():
                    if str(user_context.get(cond_key)) == str(cond_val):
                        texts.append({'text': text, 'type': text_type})
            else:
                texts.append({'text': text, 'type': text_type})
        return texts

    def get_keyboards(self, update, context):
        if self.state_type == 'question':
            return self.keyboards.to_telegram_keyboard(update, context)
        else:
            return None

    def perform_action(self, update, context):
        return self.action(update, context)

    def get_answer_params(self, update, context, answer):
        return self.keyboards.get_data_by_text(update, context, answer)

    def get_next_state(self, update, context):
        next_states = self.state_data.get('next_states', [])

        if len(next_states) == 0:
            if self.state_type == 'question':
                self.error(f'no next_state')
            return None

        if self.state_type == 'action':
            index = self.perform_action(update, context)
            if index >= len(next_states):
                return None
            if index == -1:
                raise UnknownError
            return self.States.states_map[next_states[index]['state']]

        if len(next_states) > 1:
            self.error('more than one next_state')

        return self.States.states_map[next_states[0]['state']]

    def has_error_state(self):
        error_states = self.state_data.get('error_states', [])
        return len(error_states) != 0

    def run_error_state(self, update, context):
        error_states = self.state_data.get('error_states', [])
        if len(error_states) == 0:  # default error
            self.run_default_error_state(update, context)
        else:  # specified error
            error_state = self.States.states_map[error_states[0]['state']]
            error_texts = error_state.get_texts(update, context)
            for text in error_texts:
                bot_send_message(update, context, text, remove_keyboard=False)

    def run_server_error_state(self, update, context):
        self.States.run_server_error_state(update, context)

    def run_default_error_state(self, update, context):
        self.States.run_default_error_state(update, context)

    def run_state(self, update, context):
        """
        perform the current state, send message to user
        """
        logger.info(f'{self.state_type}, {self.get_texts(update, context)}')
        if self.state_type in ['question', 'message', 'error']:
            texts = self.get_texts(update, context)
            keyboards = self.get_keyboards(update, context)
            reply_markup = None

            for t, text in enumerate(texts):
                if t == len(texts) - 1:
                    reply_markup = keyboards

                bot_send_message(update, context, text, reply_markup=reply_markup)

    def run_save_param(self, update, context):
        if self.question_type != 'contact':
            answer = get_string_from_update(update, context)
            params = self.get_answer_params(update, context, answer)

            if self.question_type == 'input':
                context.user_data.write(self.params[0], answer)
            else:
                if len(params) == 0:  # cannot find correct answer, try again
                    raise TryAgainError

                for param_key, param_val in params.items():
                    context.user_data.write(param_key, param_val)
                    context.user_data.write(f'{param_key}_timestamp', int(datetime.utcnow().timestamp() * 1000))
        else:
            try:
                phone_number = get_phone_number_from_update(update, context)
                context.user_data.write(self.params[0], phone_number)
            except:  # this error happens when user send text instead of contact
                logger.error("Expecting user to send contact but get text instead.")
                raise TryAgainError

    def error(self, msg):
        logger.error(f'State: {self.state} with State Type: {self.state_type} {msg}')
        raise UnknownError(f'State: {self.state} with State Type: {self.state_type} {msg}')
