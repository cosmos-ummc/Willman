import json
import requests

from logger import logger
from modules.error_helper import UnknownError
from modules.load_config import load_env_vars

TOKEN, BASE_URL, WEB_HOOK_URL, AUTHORIZATION, _ = load_env_vars()

headers = dict()
headers['Authorization'] = AUTHORIZATION


def get_api(url, url_type, request_params=None, request_body=None):
    """
    example url:  /client
    """
    try:
        if url_type == 'GET':
            if request_params is not None and len(request_params) != 0:
                url = BASE_URL + url + '?' + '&'.join([f'{key}={val}' for key, val in request_params.items()])

            logger.info(url)
            response = requests.get(url, headers=headers)
        elif url_type == 'PUT':
            if request_params is not None and len(request_params) != 0:
                url = BASE_URL + url + '/' + str(request_params[0])

            assert request_body is not None, 'PUT requires request_body'
            if not isinstance(request_body, str):
                request_body = json.dumps(request_body)

            logger.info(url)
            logger.info(request_body)
            response = requests.put(url, request_body, headers=headers)
        else:  # POST
            assert request_body is not None, 'POST requires request_body'
            if not isinstance(request_body, str):
                # [LU] for hackathon
                if 'userId' in request_body:
                    # request_body = json.dumps(request_body)
                    logger.info(url)
                    logger.info(request_body)
                    response = requests.post('https://chat.quaranteams.tk:443/like' , json=request_body, headers=headers)
                else:
                    request_body = json.dumps(request_body)
                    logger.info(url)
                    logger.info(request_body)
                    response = requests.post(BASE_URL + url, request_body, headers=headers)

    except:  # connection error?
        logger.error('Server connection error.')
        raise UnknownError('server connection error')

    return response
