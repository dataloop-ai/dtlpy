import logging

from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Triggers:
    """
    Triggers repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project: entities.Project = None,
                 service: entities.Service = None,
                 project_id: str = None):
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
    def service(self) -> entities.Service:
        if self._service is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "service". need to set a Service entity or use service.triggers repository')
        assert isinstance(self._service, entities.Service)
        return self._service

    @service.setter
    def service(self, service: entities.Service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid Service entity')
        self._service = service

    @property
    def project(self) -> entities.Project:
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
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def name_validation(self, name: str):
        url = '/piper-misc/naming/triggers/{}'.format(name)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

    def create(self,
               # for both trigger types
               service_id: str = None,
               trigger_type: entities.TriggerType = entities.TriggerType.EVENT,
               name: str = None,
               webhook_id=None,
               function_name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
               project_id=None,
               active=True,
               # for event trigger
               filters=None,
               resource: entities.TriggerResource = entities.TriggerResource.ITEM,
               actions: entities.TriggerAction = None,
               execution_mode: entities.TriggerExecutionMode = entities.TriggerExecutionMode.ONCE,
               # for cron triggers
               start_at=None,
               end_at=None,
               inputs=None,
               cron=None,
               **kwargs) -> entities.BaseTrigger:
        """
        Create a Trigger. Can create two types: a cron trigger or an event trigger.
        Inputs are different for each type

        Inputs for all types:

        :param service_id: Id of services to be triggered
        :param project_id: project id where trigger will work
        :param webhook_id: id for webhook to be called
        :param trigger_type: can be cron or event. use enum dl.TriggerType for the full list
        :param name: name of the trigger
        :param function_name: the fucntion name to be called when triggered. must be defined in the package
        :param active: optional - True/False, default = True

        Inputs for event trigger:
        :param filters: optional - Item/Annotation metadata filters, default = none
        :param execution_mode: how many time trigger should be activate. default is "Once". enum dl.TriggerExecutionMode
        :param resource: optional - Dataset/Item/Annotation/ItemStatus, default = Item
        :param actions: optional - Created/Updated/Deleted, default = create

        Inputs for cron trigger:
        :param start_at: iso format date string to start activating the cron trigger
        :param end_at: iso format date string to end the cron activation
        :param inputs: dictionary "name":"val" of inputs to the function
        :param cron: cron spec specifying when it should run. more information: https://en.wikipedia.org/wiki/Cron

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
            filters = filters.prepare(query_only=True).get('filter', dict())

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

        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]
        else:
            actions = [entities.TriggerAction.CREATED]

        if len(actions) == 0:
            actions = [entities.TriggerAction.CREATED]

        if trigger_type == entities.TriggerType.EVENT:
            spec = {
                'filter': filters,
                'resource': resource,
                'executionMode': execution_mode,
                'actions': actions
            }
        elif trigger_type == entities.TriggerType.CRON:
            spec = {
                'endAt': end_at,
                'startAt': start_at,
                'cron': cron,
            }
        else:
            raise ValueError('Unknown trigger type: "{}". Use dl.TriggerType for known types'.format(trigger_type))

        spec['input'] = dict() if inputs is None else inputs
        spec['operation'] = operation

        # payload
        if self._project_id is None and project_id is None:
            raise exceptions.PlatformException('400', 'Please provide a project id')
        elif project_id is None:
            project_id = self._project_id

        payload = {
            'type': trigger_type,
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
        return entities.BaseTrigger.from_json(_json=response.json(),
                                              client_api=self._client_api,
                                              project=self._project if self._project_id == project_id else None,
                                              service=self._service)

    def get(self, trigger_id=None, trigger_name=None) -> entities.BaseTrigger:
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
            trigger = entities.BaseTrigger.from_json(client_api=self._client_api,
                                                     _json=response.json(),
                                                     project=self._project,
                                                     service=self._service)
            # verify input trigger name is same as the given id
            if trigger_name is not None and trigger.name != trigger_name:
                logger.warning(
                    "Mismatch found in triggers.get: trigger_name is different then trigger.name:"
                    " {!r} != {!r}".format(
                        trigger_name,
                        trigger.name))
        else:
            if trigger_name is None:
                raise exceptions.PlatformException('400', 'Must provide either trigger name or trigger id')
            else:
                triggers = self.list(filters=entities.Filters(field='name', values=trigger_name,
                                                              resource=entities.FiltersResource.TRIGGER))
                if triggers.items_count == 0:
                    raise exceptions.PlatformException('404', 'Trigger not found')
                elif triggers.items_count == 1:
                    trigger = triggers.items[0]
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

    def update(self, trigger: entities.BaseTrigger) -> entities.BaseTrigger:
        """

        :param trigger: Trigger entity
        :return: Trigger entity
        """
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
        return entities.BaseTrigger.from_json(_json=response.json(),
                                              client_api=self._client_api,
                                              project=self._project,
                                              service=self._service)

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.BaseTrigger]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_trigger, trigger in enumerate(response_items):
            jobs[i_trigger] = pool.submit(entities.BaseTrigger._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': trigger,
                                             'project': self._project,
                                             'service': self._service})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        triggers = miscellaneous.List([r[1] for r in results if r[0] is True])
        return triggers

    def _list(self, filters: entities.Filters):
        """
        List project triggers
        :return:
        """
        url = '/query/faas'

        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project packages
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.TRIGGER)
            if self._project is not None:
                filters.add(field='projectId', values=self._project.id)
            if self._service is not None:
                filters.add(field='spec.operation.serviceId', values=self._service.id)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))

        if filters.resource != entities.FiltersResource.TRIGGER:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.TRIGGER. Got: {!r}'.format(filters.resource))

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def resource_information(self, resource, resource_type, action='Created'):
        """
        return which function should run on a item (based on global triggers)

        :param resource: 'Item' / 'Dataset' / etc
        :param resource_type: dictionary of the resource object
        :param action: 'Created' / 'Updated' / etc.

        """
        url = '/trigger-resource-information'

        payload = {'resource': resource_type,
                   'entity': resource.to_json(),
                   'action': action}
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()
