from urllib.parse import urlencode
import logging

from .. import entities, miscellaneous, exceptions

logger = logging.getLogger(name=__name__)


class Triggers:
    """
    Triggers repository
    """

    def __init__(self, client_api, project=None, service=None, project_id=None):
        self._client_api = client_api
        self._project = project
        self._service = service
        if project_id is None:
            if self._project is not None:
                project_id = self._project.id
            elif self._service is not None:
                project_id = self._service.project_id

        self._project_id = project_id

    ############
    # entities #
    ############
    @property
    def service(self):
        if self._service is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "service". need to set a Service entity or use service.triggers repository')
        assert isinstance(self._service, entities.Service)
        return self._service

    @service.setter
    def service(self, service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid Service entity')
        self._service = service

    @property
    def project(self):
        if self._project is None:
            if self._service is not None:
                self._project = self._service._project
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.triggers repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def create(self, service_id=None, webhook_id=None, name=None, filters=None, function_name=None,
               resource='Item', actions=None, active=True, execution_mode=None, project_id=None, **kwargs):
        """
        Create a Trigger

        :param function_name:
        :param project_id:
        :param webhook_id:
        :param name:
        :param execution_mode:
        :param service_id: Id of services to be triggered
        :param filters: optional - Item/Annotation metadata filters, default = none
        :param resource: optional - dataset/item/annotation, default = item
        :param actions: optional - Created/Updated/Deleted, default = create
        :param active: optional - True/False, default = True
        :return: Trigger entity
        """
        scope = kwargs.get('scope', None)
        if service_id is None and webhook_id is None:
            if self._service is not None:
                service_id = self._service.id

        # type
        if (service_id is None and webhook_id is None) or (service_id is not None and webhook_id is not None):
            raise exceptions.PlatformException('400', 'Must provide either service id or webhook id but not both')

        if name is None:
            if self._service is not None:
                name = self._service.name
            else:
                name = 'default_trigger'

        if filters is None:
            filters = dict()
        elif isinstance(filters, entities.Filters):
            filters = filters.prepare()['filter']

        if function_name is None:
            function_name = 'run'

        # actions
        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]

        if service_id is None:
            operation = {
                'type': 'webhook',
                'webhookId': webhook_id
            }
        else:
            operation = {
                'type': 'function',
                'serviceId': service_id,
                'functionName': function_name

            }

        spec = {
            'filter': filters,
            'operation': operation,
        }

        # add optionals
        if resource is not None:
            spec['resource'] = resource
        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]
            spec['actions'] = actions
        else:
            spec['actions'] = ['Created']
        if execution_mode is not None:
            spec['executionMode'] = execution_mode
        else:
            spec['executionMode'] = 'Once'

        # payload
        if self._project_id is None and project_id is None:
            raise exceptions.PlatformException('400', 'Please provide a project id')
        elif project_id is None:
            project_id = self._project_id

        payload = {
            'active': active,
            'projectId': project_id,
            'name': name,
            'spec': spec
        }

        if scope is not None:
            logger.warning(
                "Only superuser is allowed to define a trigger's scope. "
                "If you are not a superuser you will not be able to perform this action")
            payload['scope'] = scope

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
                                          project=self._project,
                                          service=self._service)

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
                                                 project=self._project,
                                                 service=self._service)
        else:
            if trigger_name is None:
                raise exceptions.PlatformException('400', 'Must provide either trigger name or trigger id')
            else:
                triggers = self.list(name=trigger_name)
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
                                          project=self._project,
                                          service=self._service)

    def list(self, active=None, page_offset=None, resource=None, service_id=None, name=None, project_id=None):
        """
        List project triggers
        :return:
        """
        url = '/triggers'
        query_params = {
            'name': name,
            'resource': resource,
            'active': active,
            'pageOffset': page_offset
        }

        # either project or service
        if project_id is None:
            if self._project_id is not None:
                project_id = self._project_id
        if service_id is None:
            if self._service is not None:
                service_id = self._service.id

        if service_id is not None:
            query_params['serviceId'] = service_id
        else:
            query_params['projects'] = project_id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        # return triggers list
        triggers = miscellaneous.List()
        for trigger in response.json()['items']:
            triggers.append(entities.Trigger.from_json(client_api=self._client_api,
                                                       _json=trigger,
                                                       project=self._project,
                                                       service=self._service))
        return triggers
