from modules import strings


class Keyboards:
    def __init__(self, keyboards_data, one_time_keyboard=False):
        self.keyboards_data = keyboards_data
        self.one_time_keyboard = one_time_keyboard
        self.keyboards = []
        for keyboard_data in keyboards_data:
            self.keyboards.append(_Keyboard(keyboard_data))

    def __len__(self):
        return len(self.keyboards)

    def to_telegram_keyboard(self, update, context):
        keyboards = []
        # multirow = len(self.keyboards) >= 3
        for keyboard in self.keyboards:
            # if multirow:
            #     keyboards.append(keyboard.to_telegram_keyboard(update, context))
            # else:
            #     keyboards.append(keyboard.to_telegram_keyboard(update, context))
            keyboards.append(keyboard.to_telegram_keyboard(update, context))
        # if not multirow:
        #     keyboards = [keyboards]
        # return ReplyKeyboardMarkup(keyboards, resize_keyboard=True, one_time_keyboard=self.one_time_keyboard)
        return keyboards

    def get_data_by_text(self, update, context, text):
        # if context.user_data.get('localization') is None:
        #     # first try
        #     for keyboard in self.keyboards:
        #         if '/ '.join(strings.Strings.get_string(keyboard.keyboard_text, all_langs=True)) == text:
        #             return keyboard.params
        #
        #     # second try
        #     for keyboard in self.keyboards:
        #         if text in strings.Strings.get_string(keyboard.keyboard_text, all_langs=True):
        #             return keyboard.params
        # else:
        #     for keyboard in self.keyboards:
        #         if strings.Strings.get_string(keyboard.keyboard_text, context=context) == text:
        #             return keyboard.params

        # this implementation is O(N*M), N = keyboard texts, M = possible languages
        # find someone to optimize this

        # first try
        for keyboard in self.keyboards:
            ret_text = strings.Strings.get_string(keyboard.keyboard_text, context=context)
            if isinstance(ret_text, list):
                # if user no language, but user input same as keyboard text
                if '/ '.join(ret_text) == text:
                    return keyboard.params
            else:
                if ret_text == text:  # if user input same as keyboard text
                    return keyboard.params

        # second try, in case unknown error,
        for keyboard in self.keyboards:
            ret_text = strings.Strings.get_string(keyboard.keyboard_text, context=context)
            if text in ret_text:  # if ret_text is a list or str and text in ret_text (works for both string or list)
                return keyboard.params

        return {}


class _Keyboard:
    def __init__(self, keyboard_data):
        keyboard_text = keyboard_data['text']
        keyboard_type = keyboard_data.get('type', 'text')

        self.keyboard_text = keyboard_text
        self.keyboard_type = keyboard_type
        self.params = {}

        if keyboard_type == 'text':
            keyboard_param_data = keyboard_data['data']
            for param_key, param_val in keyboard_param_data.items():
                self.params[param_key] = param_val

    def to_telegram_keyboard(self, update, context):
        text = strings.Strings.get_string(self.keyboard_text, context=context)
        if isinstance(text, list):
            texts = text
            if len(texts) > 1 and texts[0] != texts[1]:
                # text = '/ '.join(texts) [LU] integration testing purpose, as the taml currently does not support chinese and malay language
                text = ''.join(texts)
            else:
                # it is possible that user define texts of all language in every language
                # e.g. EN: Hi Ni hao
                # e.g. CN: Hi Ni hao
                text = texts[0]

        # if context.user_data.get('localization') is None:
        #     texts = strings.Strings.get_string(self.keyboard_text, all_langs=True)
        #     if len(texts) != 0 and texts[0] != texts[1]:
        #         text = '/ '.join(strings.Strings.get_string(self.keyboard_text, all_langs=True))
        #     else:
        #         text = texts[0]
        # else:
        #     text = strings.Strings.get_string(self.keyboard_text, context=context)

        if self.keyboard_type == 'contact':
            return {'text': text, 'type': 'contact'}
        else:
            return {'text': text, 'type': 'normal'}

