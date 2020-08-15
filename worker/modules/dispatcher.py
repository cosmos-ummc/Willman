import re
from threading import Thread


class Handler:
    def __init__(self, keyword: str, callback: callable):
        self.keyword = keyword
        self.callback = callback


class Dispatcher(Thread):

    def __init__(self, update, context):
        Thread.__init__(self)
        self.handlers = []
        self.update = update
        self.context = context

    def add_hanlder(self, handler: Handler):
        self.handlers.append(handler)

    def extract_command(self, text_message: str):
        if len(text_message.split()) is not 1:
            return None
        pattern = re.compile(r'(?<=/)(\w+)')
        result = pattern.search(text_message)
        if result is not None:
            return result.group(1)
        else:
            return None

    def process_incoming_message(self, incoming_message):
        incoming_message_text = str(incoming_message['text'])
        command = self.extract_command(incoming_message_text)

        if command is not None:
            appointed_handler = [handler for handler in self.handlers if handler.keyword == command]
        else:
            appointed_handler = [handler for handler in self.handlers if handler.keyword == "all"]

        appointed_handler[0].callback(self.update, self.context)

    def run(self):
        self.process_incoming_message(self.update)
