import xlrd
import yaml

from logger import logger


class _Strings:
    def __init__(self):
        self.strings_dict = None
        self.localizations = []
        self.map_lang_to_loc = {  # todo: setup from config file
        # [LU] changed to integer to comply with standards from question builder (originally as sting)
            'ENGLISH': 1,
            'BAHASA MELAYU': 2,
            '中文': 3,
            # 'TAMIL': '4'
        }
        self.localizations = self.map_lang_to_loc.values()

    def load_strings(self, fn):
        book = xlrd.open_workbook(fn, encoding_override="cp1252")
        sheet = book.sheets()[0]
        strings_dict = {}

        for i, row in enumerate(sheet.get_rows()):
            if i == 0:
                headers = [self.map_lang_to_loc[col.value] for col in row if col.value != '']
            else:
                key = row[0].value
                if len(key) == 0:  # meaning it read empty first column, it should be ended
                    continue
                row = [col.value for col in row][1:]  # first one is key, so ignore first
                strings_dict[key] = {header: col.strip() for header, col in zip(headers, row)}
        self.strings_dict = strings_dict
        # logger.info(f'{strings_dict}')
        return self

    def get_string(self, key, update=None, context=None, all_langs=False):
        """
        key='MISC_BOT_DO_NOT_UNDERSTAND'
        lang='EN|CN|BM'

        return: language specific output
        """
        assert hasattr(self, 'strings_dict'), 'Please call Strings.load_strings(fn)'
        assert self.strings_dict is not None, 'Please call Strings.load_strings(fn)'

        if all_langs:
            return [self.strings_dict[key][loc] for loc in self.localizations]

        if context is None:
            loc = '1'
        else:
            # get api
            loc = context.user_data.get('localization', '1')

        if key not in self.strings_dict:
            # this is the key we put in the code, therefore only happened in development.
            raise ValueError(key + ' is not in strings_dict, this cannot be happened, please check the code')

        if loc not in self.localizations:  # set to eng if language not available?
            # logger.warning(f'Patient localization ({loc}) is not in predefined localizations, '
            #                 f'default localization is used: 1')

            # loc might be 0 or None, so returning all_langs
            return self.get_string(key, update, context, True)

        # if loc is None:  # localization in user_data but is set to None
        #     loc = 1

        return self.strings_dict[key][loc]


class _StringsV2(_Strings):
    """
    this is to configure for yaml structure
    """

    def __init__(self):
        super().__init__()

    def load_strings(self, fn):
        # override version 1 strings method
        f = open(fn, 'r', encoding='utf8')
        fsm_structure = yaml.load(f, yaml.FullLoader)

        localizations = fsm_structure['localizations']
        texts = fsm_structure['texts']
        strings_dict = {}

        self.map_lang_to_loc = {str(k): str(v) for k, v in localizations.items()}
        logger.info(f'{self.map_lang_to_loc}')

        for key in texts:  # text_key, e.g. WELCOME_MESSAGE
            # e.g. EN: welcome <br> BM: selamat datang
            text_struct = texts[key]

            # e.g. strings_dict['WELCOME_MESSAGE'] = {1: welcome, 2: selamat datang}
            strings_dict[key] = {localizations[lang]: text.strip() for lang, text in text_struct.items()}

        self.strings_dict = strings_dict
        logger.info(f'{strings_dict}')
        return self


def init_string(fn='res/cosmos_text.xlsx', load_v2=False):
    """
    must run this when init the bot
    """
    global Strings
    logger.info('Initialize Strings')
    if not load_v2:
        StringsClass = _Strings
    else:
        StringsClass = _StringsV2

    Strings = StringsClass().load_strings(fn)


Strings = None  # type: _Strings

if __name__ == '__main__':
    init_string('../res/cosmos.yaml', True)
    init_string('../res/cosmos_text.xlsx', False)

