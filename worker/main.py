from flask import Flask
from flask_restful import Resource, Api, reqparse

from context import Context
from message import redis_conn

from modules.message_filter import process_text
from modules import fsm, strings
from modules.dispatcher import Dispatcher, Handler
from modules.command_helper import generic_command

from logger import logger

app = Flask(__name__)
api = Api(app)

# initialization
fsm.init_states('res/cosmos.yaml')
# strings.init_string('res/cosmos_text.xlsx')  # loading excel
strings.init_string('res/cosmos.yaml', True)


class Worker(Resource):
    # health check
    def get(self):
        logger.info('GET success. Status OK.')
        return {'status': 'OK'}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('text')
        parser.add_argument('chat_id')
        parser.add_argument('date')
        parser.add_argument('phone_number')
        payload = parser.parse_args()
        logger.info(f'Incoming payload: {payload}')

        # hard coded response for testing purpose
        #         msg = {
        #             'chat_id'       : payload['chat_id'],
        #             'text'          : 'Welcome to UMMC Covid-19 Home Monitoring System.\n\nSelamat datang ke Sistem Pemantauan Covid-19 PPUM.\n\n欢迎来到马大医院新冠肺炎症状监测系统。',
        #             'reply_markup'  : [
        #                 {
        #                     "text":"Start/ Mula/ 开始",
        #                     "type":"normal"
        #                 },
        #                 {
        #                     "text":"Say Hi",
        #                     "type":"normal"
        #                 },
        #                 {
        #                     "text":"Say Hi",
        #                     "type":"normal"
        #                 },
        #                 {
        #                     "text":"Say Hi",
        #                     "type":"normal"
        #                 }
        #             ]
        #         }
        #         response = {'user': payload['user'], 'msg': msg}
        #         r.rpush('sending_queue', json.dumps(response))

        # Context initialization here
        context = Context(chat_id=payload['chat_id'], redis_conn=redis_conn)

        dp = Dispatcher(payload, context)

        for command_state_id in fsm.States.commands:
            command = fsm.States.states_map[command_state_id].command.command
            dp.add_hanlder(Handler(command, generic_command(command_state_id)))

        dp.add_hanlder(Handler('all', process_text))
        dp.start()
        dp.join()

        return {'status': 'Message added to sending queue'}


api.add_resource(Worker, '/worker')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)

