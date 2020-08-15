from telethon.tl.custom.button import Button
from telethon.tl.types import ReplyKeyboardHide
from telethon import TelegramClient, events


# 
# > Factory that produces required button(s) based on provided parameters
# TODO: arrange button
def button_factory_method(reply_markup):
    try:
        if len(reply_markup) == 1 and reply_markup[0]['type'].upper() == "REMOVE":
            return ReplyKeyboardHide(True)
        elif len(reply_markup) == 0:
            pass 
        elif len(reply_markup) == 2:
            return [Button.text(btns['text'], resize=True) for btns in reply_markup]
        else:
            for buttons in reply_markup:
                if buttons['type'].upper() == 'CONTACT':
                    return [[Button.request_phone(btns['text'], resize=True)] for btns in reply_markup]
                else:
                    return [[Button.text(btns['text'], resize=True)] for btns in reply_markup]            
    except:
        pass


# 
# > Method to extract user phone number from contact object
# 
def get_phone_number(newMessage):
    return '' if newMessage.media is None else newMessage.media.phone_number 