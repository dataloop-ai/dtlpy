from .. import entities, repositories, miscellaneous, exceptions


class Triggers:
    """
    Triggers repository
    """

    def __init__(self, client_api, project=None, deployment=None):
        self._client_api = client_api
        self._project = project
        self.deployment = deployment

    @property
    def project(self):
        if self._project is None:
            if self.deployment is None:
                self._project = repositories.Projects(client_api=self._client_api).get()
            else:
                self._project = self.deployment.project
        assert isinstance(self._project, entities.Project)
        return self._project

    # noinspection PyPep8Naming
    def create(self, deployment_id, name=None, filters=None,
               resource=None, actions=None, active=True, executionMode=None):
        """
        Create a Trigger

        :param name:
        :param executionMode:
        :param deployment_id: Id of deployments to be triggered
        :param filters: optional - Item/Annotation metadata filters, default = none
        :param resource: optional - dataset/item/annotation, default = item
        :param actions: optional - Created/Updated/Deleted, default = create
        :param active: optional - True/False, default = True
        :return: Trigger entity
        """
        # defaults
        if name is None:
            name = 'default_trigger'
        if filters is None:
            filters = dict()
        elif isinstance(filters, entities.Filters):
            filters = filters.prepare()['filter']

        # actions
        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]

        # payload
        payload = {'deploymentId': deployment_id,
                   'project': self.project.id,
                   'filter': filters,
                   'active': active,
                   'name': name,
                   'special': True}

        # add optionals
        if resource is not None:
            payload['resource'] = resource
        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]
            payload['actions'] = actions
        else:
            payload['actions'] = ['Created']
        if executionMode is not None:
            payload['executionMode'] = executionMode
        else:
            payload['executionMode'] = 'Once'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/triggers',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Trigger.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self.project)

    def get(self, trigger_id=None, trigger_name=None):
        """
        Get Trigger object

        :param trigger_name:
        :param trigger_id:
        :return: Trigger object
        """
        # request
        if trigger_id is not None:
            success, response = self._client_api.gen_request(
                req_type="get",
                path="/triggers/{}".format(trigger_id)
            )

            # exception handling
            if not success:
                raise exceptions.PlatformException(response)

            # return entity
            trigger = entities.Trigger.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 project=self.project)
        else:
            if trigger_name is None:
                raise exceptions.PlatformException('400', 'Must provide either trigger name or trigger id')
            else:
                triggers = self.list()
                triggers = [trigger for trigger in triggers if trigger.name == trigger_name]
                if len(triggers) == 0:
                    raise exceptions.PlatformException('404', 'Trigger not found')
                elif len(triggers) == 1:
                    trigger = triggers[0]
                else:
                    raise exceptions.PlatformException('404',
                                                       'More than one trigger by name {} exist'.format(trigger_name))

        return trigger

    def delete(self, trigger_id=None, trigger_name=None):
        """
        Delete Trigger object

        :param trigger_name:
        :param trigger_id:
        :return: True
        """
        if trigger_id is None:
            if trigger_name is None:
                raise exceptions.PlatformException('400', 'Must provide either trigger name or trigger id')
            else:
                trigger_id = self.get(trigger_name=trigger_name).id
        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/triggers/{}".format(trigger_id)
        )
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        return True

    def update(self, trigger):
        """

        :param trigger: Trigger entity
        :return: Trigger entity
        """
        assert isinstance(trigger, entities.Trigger)

        # payload
        payload = trigger.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/triggers/{}'.format(trigger.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Trigger.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self.project)

    def list(self, active=None, page_offset=None, resource=None):
        """
        List project triggers
        :return:
        """
        url_path = '/triggers'
        query = list()

        # either project or deployment
        if self.project is not None:
            query.append('projects={}'.format(self.project.id))
        elif self.deployment is not None:
            query.append('deploymentId={}'.format(self.deployment.id))

        # other queries
        if active is not None:
            query.append('active={}'.format(active).lower())
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))
        if resource is not None:
            query.append('resource={}'.format(resource))

        if len(query) > 0:
            query_string = '&'.join(query)
            url_path = '{}?{}'.format(url_path, query_string)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        # return triggers list
        triggers = miscellaneous.List()
        for trigger in response.json()['items']:
            triggers.append(entities.Trigger.from_json(client_api=self._client_api,
                                                       _json=trigger,
                                                       project=self.project))
        return triggers
