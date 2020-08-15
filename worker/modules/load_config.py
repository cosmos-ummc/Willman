import os
import sys

from logger import logger


def load_env_vars():
    BOT_TOKEN = os.environ['BOT_TOKEN']
    WEB_HOOK_URL = os.environ['WEB_HOOK_URL']

    API_BASE_URL = os.environ['API_BASE_URL']
    API_AUTHORIZATION_TOKEN = os.environ['API_AUTHORIZATION_TOKEN']

    # MONGO_DB_ENDPOINT = os.environ['MONGO_DB_ENDPOINT']

    try:
        assert (BOT_TOKEN and WEB_HOOK_URL and API_BASE_URL and API_AUTHORIZATION_TOKEN)
    except AssertionError:
        logger.error('Fatal Error: Failed to load environment variables. Stopping the bot...')
        sys.exit(1)

    return BOT_TOKEN, API_BASE_URL, WEB_HOOK_URL, API_AUTHORIZATION_TOKEN, None
