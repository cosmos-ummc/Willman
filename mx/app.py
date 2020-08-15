import os
import json
import logging

import redis
import asyncio
import requests

import telethon_helper

from telethon import TelegramClient, events
from telethon.network.connection.tcpfull import ConnectionTcpFull
from telethon.tl.custom.button import Button
from telethon.tl.types import ReplyKeyboardHide, InputMediaPhotoExternal
from telethon.tl.functions.messages import SendMediaRequest
from telethon.errors import MultiError


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger('DEBUG')


API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
client = TelegramClient('LU', API_ID, API_HASH)


r = redis.Redis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'])
loop = asyncio.get_event_loop()
messageQueu = []

async def poll():
    while True:
        global r
        global messageQueu
        # atomic operation of getting all items in queue and delete it afterwards
        pipe = r.pipeline()
        pipe.lrange('sending_queue', 0, -1)
        pipe.delete('sending_queue')
        messageQueu.extend(pipe.execute()[0])

        # > For Context Switching purpose
        await asyncio.sleep(0.1)



async def send():
    while True:
        global messageQueu
        if messageQueu != []:

            # > Expected JSON Response: 
            #     {
            #         chat_id: 12345
            #         text: "text or URL (if URL is intended to be sent as text, indicate in 'type' parameter)"
            #         reply_markup: []
            #         type: "photo" || "video" || "file" || "text" || "remove"
            #     }
            messageQueu_ = [json.loads(msg) for msg in messageQueu]
            messageQueu.clear()


            for msg in messageQueu_:

                # > Construct KeyboardMarkup using self defined Factory Method from telethon_helper module
                buttons = telethon_helper.button_factory_method(msg['reply_markup'])

                # > Make use of client API to send media with URL/ file path/ file id on telegram server (if file exist on telegram server), all are valid
                # > Send text if type is other than listed file type
                try:
                    
                    if msg['type'].upper() == 'PHOTO':

                        await client.send_file(int(msg['chat_id']), msg['text'], buttons = buttons)

                    elif msg['type'].upper() == 'VIDEO':

                        await client.send_file(int(msg['chat_id']), msg['text'], buttons = buttons, video_note = True)

                    elif msg['type'].upper() == 'FILE':

                        await client.send_file(int(msg['chat_id']), msg['text'], buttons = buttons, force_document=True)

                    else:

                        await client.send_message(int(msg['chat_id']), msg['text'], buttons = buttons)

                except:
                    pass
                    logger.info('Eror sending message.')

                

        # > For Context Switching purpose
        await asyncio.sleep(0.1)



@client.on(events.NewMessage)
async def my_event_handler(event):
    
    # > Extraxt required fields for the use of worker nodes
    # > Template required by worker node:
    #     {
    #         text: "message text" (str),
    #         chat_id: "chat_id" (str),
    #         date: "date" (datetime.datetime)
    #         phone_number: "+60143360623"
    #     }
    msg = {
        "text"          : event.message.message,
        "chat_id"       : event.chat_id,
        "date"          : event.message.date,
        "phone_number"  : telethon_helper.get_phone_number(event)
    }
    requests.post(f'http://{os.environ["WORKER_HOST"]}:{os.environ["WORKER_PORT"]}/worker', data=msg)

client.start(bot_token=BOT_TOKEN)
loop.create_task(send())
loop.create_task(poll())
client.run_until_disconnected()

################################################################################################################################################################################

        # Response for video:
        # {
        #     chat_id: 12345
        #     text: "file/path/to/video.mp4 or url"
        #     reply_markup: []
        #     type: "video"
        # }

        # Response for photo:
        # {
        #     chat_id: 12345
        #     text: "file/path/to/photo.jpg or url"
        #     reply_markup: []
        #     type: "photo"
        # }

        # Response for text:
        # {
        #     chat_id: 12345
        #     text: "message to deliver"
        #     reply_markup: []
        #     type: "text"
        # }