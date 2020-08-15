import json
from collections import OrderedDict

from logger import logger
from modules import context_helper, api_helper
from modules.error_helper import UnknownError


class RegistrationStatus:  # deprecated
    NOT_REGISTERED = 100
    INCOMPLETE = 101
    COMPLETE = 102


def if_else_condition(if_condition, condition_type):
    if_condition_temp = {}
    for if_key, if_val in if_condition.items():
        if isinstance(if_val, list):
            if_condition_temp[if_key] = [str(v) for v in if_val]
        else:
            if_condition_temp[if_key] = str(if_val)
    if_condition = if_condition_temp

    def f(update, context):
        # init res
        if condition_type == 'and':
            # if no and condition happens, this remain True
            res = True
        else:
            # if no or condition happens, this remain False
            res = False

        logger.info(if_condition)

        for if_key, if_val in if_condition.items():
            logger.info(f'{if_key} {context.user_data.get(if_key)}')
            if isinstance(if_val, list):
                if_compare = context.user_data.get(if_key) in if_val
            else:
                if_compare = context.user_data.get(if_key) == if_val
            if condition_type == 'and':
                res = res and if_compare
            else:
                res = res or if_compare

        if res:
            return 0
        else:
            return 1

    return f


def _webhook_store_param(response_json, data_to_store, context):
    for key in response_json:
        if key in data_to_store:
            # e.g. registrationStatus: patient_type
            # the expected logic is like below:
            # context.user_data['patient_type'] = response_json['registrationStatus']
            key_to_store = data_to_store[key]
            if isinstance(key_to_store, (dict, OrderedDict)):
                _webhook_store_param(response_json[key], key_to_store, context)
            else:
                if 'INT_' in key_to_store:
                    key_to_store = key_to_store.replace('INT_', '')
                    context.user_data.write(key_to_store, int(response_json[key]))
                elif 'STR_' in key_to_store:
                    key_to_store = key_to_store.replace('STR_', '')
                    context.user_data.write(key_to_store, str(response_json[key]))
                else:
                    context.user_data.write(key_to_store, response_json[key])
    logger.info(f'the patient id num is :{context.user_data.get("id_num")}')


def webhook(url, url_type, request_params=None, request_body=None, data_to_store=None):
    def f(update, context):
        chat_id, message = context_helper.get_current_context(update, context)
        context.user_data.write('chat_id', chat_id)

        if request_params is not None:
            if isinstance(request_params, list):
                real_request_params = [context.user_data.get(val) for val in request_params]
            else:
                real_request_params = {key: context.user_data.get(val) for key, val in request_params.items()}
        else:
            real_request_params = None

        if request_body is not None:
            real_request_body = {}
            otherparams = {}
            for key, val in request_body.items():
                if 'STR_' in val:
                    val = val.replace('STR_', '')
                    # [LU] code below are modified for hackathon purpose, the request parameter formatting has changed
                    if key.upper() == 'PATIENTID':
                        real_request_body[key] = val
                    else :
                        otherparams[key] = str(context.user_data.get(val))
                elif 'INT_' in val:
                    val = val.replace('INT_', '')
                    # [LU] code below are modified for hackathon purpose, the request parameter formatting has changed
                    if key.upper() == 'PATIENTID':
                        real_request_body[key] = val
                    else :
                        otherparams[key] = int(context.user_data.get(val))
                else:  # default case, ignore casting
                    # [LU] code below are modified for hackathon purpose, the request parameter formatting has changed
                    if key.upper() == 'PATIENTID':
                        logger.info(f'The key to refer in storage is: {val}')
                        logger.info(f'All data are: {context.user_data.get_all()}')
                        logger.info(f'The patientId is: {context.user_data.get(val)}')
                        real_request_body[key] = context.user_data.get(val)
                    else :
                        otherparams[key] = context.user_data.get(val)

            # [LU] code below are modified for hackathon purpose, the request parameter formatting has changed
            if 'patientId' in real_request_body:
                real_request_body['data'] = otherparams
            else:
                real_request_body = otherparams
                    
            # real_request_body = {key: context.user_data[val] for key, val in request_body.items()}
        else:
            real_request_body = None

        logger.info(f'The request body sent is :{real_request_body}')
        response = api_helper.get_api(url, url_type, real_request_params, real_request_body)

        # ####### if response.status_code not in [200, 404], raise error here, caught by telegram bot by default
        if response.status_code != 200:
            raise UnknownError(f'server status code: {response.status_code}')

        ####### if response.status_code not in [200, 404], raise error here, caught by telegram bot by default
        # if response.status_code != 200 and url_type != 'PUT':  # hard code here!!
        #     raise UnknownError(f'server status code: {response.status_code}')

        response_json = json.loads(response.text)

        ############## hard code changes until backend have new implementation

        # if url == '/v1/client/patients' and url_type == 'GET':
        #     response_json_temp = {}
        #     patients = response_json['patients']
        #     logger.info(patients)
        #
        #     if not patients or len(patients) == 0:
        #         response_json_temp['registrationStatus'] = RegistrationStatus.NOT_REGISTERED
        #
        #     elif patients[0]['telegramId'] and patients[0]['phoneNumber']:
        #         response_json_temp['registrationStatus'] = RegistrationStatus.COMPLETE
        #
        #     elif patients[0]['phoneNumber']:
        #         response_json_temp['registrationStatus'] = RegistrationStatus.INCOMPLETE
        #
        #     if patients is not None and len(patients) != 0:
        #         response_json_temp['status'] = patients[0]['status']
        #         response_json_temp['id'] = patients[0]['id']
        #
        #         if response_json_temp['registrationStatus'] == RegistrationStatus.COMPLETE:
        #             response_json_temp['localization'] = int(patients[0]['localization'])
        #
        #     response_json = response_json_temp

        logger.info(f'{response.status_code}')

        # if url == '/v1/client/patients' and url_type == 'PUT':
        #     response_json_temp = {}
        #     if response.status_code == 200:
        #         response_json_temp['registrationStatus'] = RegistrationStatus.COMPLETE
        #     else:
        #         response_json_temp['registrationStatus'] = RegistrationStatus.NOT_REGISTERED
        #
        #     response_json = response_json_temp

        # [LU] for hackathon
        formatted_response_json = {}
        formatted_data_to_store = {}
        if 'patients' in response_json:
            if len(response_json["patients"]) > 0:
                formatted_response_json = response_json["patients"][0]
                formatted_data_to_store = data_to_store['data']
            else:
                formatted_response_json = {"registrationStatus":"0"}
                formatted_data_to_store = data_to_store['data']
        elif 'registrationStatus' in response_json:
            formatted_response_json['data'] = response_json
            formatted_data_to_store = data_to_store
            logger.info(formatted_response_json)
        elif 'hasSymptom' in response_json:
            formatted_response_json = response_json
            formatted_data_to_store = data_to_store['data']
            logger.info(formatted_response_json)
        else:
            formatted_response_json = response_json
            formatted_data_to_store = data_to_store
        
        logger.info(f'{response_json}')
        logger.info(f'{data_to_store}')
        logger.info(f'{context.user_data.get_all()}')
        ############## map responseJson to bot memory
        if data_to_store is not None:
            _webhook_store_param(formatted_response_json, formatted_data_to_store, context)

        logger.info(f'{data_to_store}')
        logger.info(f'{context.user_data.get_all()}')

        return 0

    return f


def set_variable(params_to_set):
    def f(update, context):
        for key, val in params_to_set.items():
            if key in context.user_data:
                if isinstance(val, str):
                    if 'INT_' in val:
                        val = int(val.replace('INT_', ''))
                    elif 'STR_' in val:
                        val = str(val.replace('STR_', ''))

                if val is not None and val == 'null':
                    val = None

                context.user_data.write(key, val)
        return 0

    return f


def get_action(action, **kwargs):
    if action == 'if_else_condition':
        return if_else_condition(kwargs['if_condition'], kwargs['condition_type'])
    elif action == 'webhook':
        return webhook(kwargs['url'], kwargs['url_type'],
                       kwargs.get('request_params'), kwargs.get('request_body'), kwargs.get('data_to_store'))
    else:
        return set_variable(kwargs['params_to_set'])


def _test_webhook_store_param():
    data_to_store = {
        'data': {
            'secondLevel': 'second_level'
        },
        'firstLevel': 'first_level'
    }
    response_json = {
        'data': {
            'secondLevel': 1
        },
        'firstLevel': 2
    }

    class DummyContext:
        def __init__(self):
            self.user_data = {}

    context = DummyContext()
    _webhook_store_param(response_json, data_to_store, context)
    logger.info(f'{context.user_data}')


if __name__ == '__main__':
    #### test webhook
    _test_webhook_store_param()
