import json
import redis
import os

from logger import logger

class Message(dict):

    def __init__(self, body):
        self.user = body.get('user')
        self.text = body.get('text')
        self.chat_id = body.get('chat_id')

    def __repr__(self):
        return repr(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def dump_json(self):
        # can add conditioning here
        return json.dumps(self.__dict__)


class MessageHandler:

    def __init__(self, redis_conn: redis.Redis):
        self.redis_conn = redis_conn

    def send_to_pool(self, message):
        json_request = json.dumps(message)
        logger.info(f'Sending >>> {json_request}')
        return self.redis_conn.rpush('sending_queue', json_request)


redis_conn = redis.Redis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], decode_responses=True)
message_handler = MessageHandler(redis_conn)