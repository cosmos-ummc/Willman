from modules import fsm_actions


class Action:
    def __init__(self, action_data):
        self.action_data = action_data

        self.action = action_data['action']
        self.params = action_data.get('params', [])

        if self.action == 'if_else_condition':
            self.condition_type = action_data['if_condition'].pop('condition_type', 'and')
            self.action_func = fsm_actions.get_action(self.action, if_condition=action_data['if_condition'],
                                                      condition_type=self.condition_type)
        elif self.action == 'webhook':
            self.action_func = fsm_actions.get_action(self.action, url=action_data['url'],
                                                      url_type=action_data['url_type'],
                                                      request_params=action_data.get('request_params'),
                                                      request_body=action_data.get('request_body'),
                                                      data_to_store=self.params)
        elif len(self.params) != 0:
            self.action_func = fsm_actions.get_action(self.action, params=self.params)
        else:
            self.action_func = fsm_actions.get_action(self.action)

    def __call__(self, update, context):
        return self.action_func(update, context)
