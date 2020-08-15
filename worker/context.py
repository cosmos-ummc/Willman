import redis


class Context:

    def __init__(self, redis_conn: redis.Redis, chat_id: int):
        self.redis_conn = redis_conn
        self.chat_id = chat_id
        self.user_data = self.UserData(self.redis_conn, self.chat_id)

    class UserData:

        def __init__(self, redis_conn: redis.Redis, chat_id: int):
            self.redis_conn = redis_conn
            self.chat_id = chat_id

        # return None if find nothing
        def get(self, key, default=None):
            result = self.redis_conn.hget(self.chat_id, key)

            if result == 'None':
                return None
            elif result == 'True':
                return True
            elif result == 'False':
                return False
            else:
                if result:
                    return result
                return default

        # return empty dictionary if find nothing
        def get_all(self):
            return self.redis_conn.hgetall(self.chat_id)

        def write(self, key, value):
            value_to_write = None
            if value is None:
                value_to_write = 'None'
            elif value is True:
                value_to_write = 'True'
            elif value is False:
                value_to_write = 'False'
            else:
                value_to_write = value

            # print("DEBUG: value to write >>", value_to_write)
            return self.redis_conn.hset(self.chat_id, key, value_to_write)

        def clear(self):
            return self.redis_conn.delete(self.chat_id)
