import datetime
import inspect
import logging
import json
import os
import tempfile
import time
from typing import Union, List, Callable
from .. import miscellaneous, exceptions, entities, repositories, assets, ApiClient, _api_reference
from ..__version__ import version as __version__

logger = logging.getLogger(name='dtlpy')
FUNCTION_END_LINE = '[Done] Executing function.'
MAX_WAIT_TIME = 8


class Services:
    """
    Services Repository

    The Services class allows the user to manage services and their properties. Services are created from the packages users create.
    See our documentation for more information about `services <https://developers.dataloop.ai/tutorials/faas/advance/chapter/>`_.
    """

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 package: entities.Package = None,
                 project_id=None, model_id=None):
        self._client_api = client_api
        self._package = package
        self._project = project
        if project_id is None:
            if project is not None:
                project_id = project.id
        self._project_id = project_id
        self._model_id = model_id
        self._settings = repositories.Settings(project=project, client_api=client_api)

    ############
    # entities #
    ############
    @property
    def package(self) -> entities.Package:
        if self._package is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT package entity in services repository. Please set a package')
        assert isinstance(self._package, entities.Package)
        return self._package

    @package.setter
    def package(self, package: entities.Package):
        if not isinstance(package, entities.Package):
            raise ValueError('Must input a valid package entity')
        self._package = package

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # try to get from package
            if self._package is not None:
                self._project = self._package._project

        if self._project is None:
            # try to get checked out project
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in services repository. Please set a project')
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/services".format(self.project.id))

    def open_in_web(self,
                    service: entities.Service = None,
                    service_id: str = None,
                    service_name: str = None):
        """
        Open the service in web platform

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param str service_name: service name
        :param str service_id: service id
        :param dtlpy.entities.service.Service service: service entity

        **Example**:

        .. code-block:: python

            package.services.open_in_web(service_id='service_id')
        """
        if service_name is not None:
            service = self.get(service_name=service_name)
        if service is not None:
            service.open_in_web()
        elif service_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(service_id) + '/main')
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def __get_from_cache(self) -> entities.Service:
        service = self._client_api.state_io.get('service')
        if service is not None:
            service = entities.Service.from_json(_json=service,
                                                 client_api=self._client_api,
                                                 project=self._project,
                                                 package=self._package)
        return service

    def checkout(self,
                 service: entities.Service = None,
                 service_name: str = None,
                 service_id: str = None):
        """
        Checkout (switch) to a service.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.service.Service service: Service entity
        :param str service_name: service name
        :param str service_id: service id

        **Example**:

        .. code-block:: python

            package.services.checkout(service_id='service_id')
        """
        if service is None:
            service = self.get(service_name=service_name, service_id=service_id)
        self._client_api.state_io.put('service', service.to_json())
        logger.info('Checked out to service {}'.format(service.name))

    ###########
    # methods #
    ###########
    @_api_reference.add(path='/services/{id}/revisions', method='get')
    def revisions(self,
                  service: entities.Service = None,
                  service_id: str = None):
        """
        Get service revisions history.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        You must provide at leats ONE of the following params: service, service_id

        :param dtlpy.entities.service.Service service: Service entity
        :param str service_id: service id

        **Example**:

        .. code-block:: python

            service_revision = package.services.revisions(service_id='service_id')
        """
        if service is None and service_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='must provide an identifier in inputs: "service" or "service_id"')
        if service is not None:
            service_id = service.id

        success, response = self._client_api.gen_request(
            req_type="get",
            path="/services/{}/revisions".format(service_id))
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/services/{id}', method='get')
    def get(self,
            service_name=None,
            service_id=None,
            checkout=False,
            fetch=None
            ) -> entities.Service:
        """
        Get service to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param str service_name: optional - search by name
        :param str service_id: optional - search by id
        :param bool checkout: if true, checkout (switch) to service
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Service object
        :rtype: dtlpy.entities.service.Service

        **Example**:

        .. code-block:: python

            service = package.services.get(service_id='service_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if service_name is None and service_id is None:
            service = self.__get_from_cache()
            if service is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Service was found, must checkout or provide an identifier in inputs')

        elif fetch:
            if service_id is not None:
                success, response = self._client_api.gen_request(
                    req_type="get",
                    path="/services/{}".format(service_id)
                )
                if not success:
                    raise exceptions.PlatformException(response)
                service = entities.Service.from_json(client_api=self._client_api,
                                                     _json=response.json(),
                                                     package=self._package,
                                                     project=self._project)
                # verify input service name is same as the given id
                if service_name is not None and service.name != service_name:
                    logger.warning(
                        "Mismatch found in services.get: service_name is different then service.name:"
                        " {!r} != {!r}".format(
                            service_name,
                            service.name))
            elif service_name is not None:
                filters = entities.Filters(resource=entities.FiltersResource.SERVICE,
                                           field='name',
                                           values=service_name,
                                           use_defaults=False)
                if self._project_id is not None:
                    filters.add(field='projectId', values=self._project_id)
                if self._package is not None:
                    filters.add(field='packageId', values=self._package.id)
                services = self.list(filters=filters)
                if services.items_count > 1:
                    raise exceptions.PlatformException('404', 'More than one service with same name. '
                                                              'Please get services from package/project entity')
                elif services.items_count == 0:
                    raise exceptions.PlatformException('404', 'Service not found: {}.'.format(service_name))
                service = services.items[0]
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Service was found, must checkout or provide an identifier in inputs')
        else:
            service = entities.Service.from_json(_json={'id': service_id,
                                                        'name': service_name},
                                                 client_api=self._client_api,
                                                 project=self._project,
                                                 package=self._package,
                                                 is_fetched=False)

        assert isinstance(service, entities.Service)
        if checkout:
            self.checkout(service=service)
        return service

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Service]:
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, service in enumerate(response_items):
            jobs[i_service] = pool.submit(entities.Service._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': service,
                                             'package': self._package,
                                             'project': self._project})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        url = '/query/faas'
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    @_api_reference.add(path='/query/faas', method='post')
    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List all services (services can be listed for a package or for a project).

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            services = package.services.list()
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.SERVICE)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.SERVICE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.SERVICE. Got: {!r}'.format(filters.resource))
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)
        elif self._project_id is not None:
            filters.add(field='projectId', values=self._project_id)
        if self._package is not None:
            filters.add(field='packageId', values=self._package.id)
        if self._model_id is not None:
            filters.add(field='metadata.ml.modelId', values=self._model_id)
        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    @_api_reference.add(path='/services/{id}/status', method='post')
    def status(self, service_name=None, service_id=None):
        """
        Get service status.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        You must provide at least ONE of the following params: service_id, service_name

        :param str service_name: service name
        :param str service_id: service id
        :return: status json
        :rtype: dict

        **Example**:

        .. code-block:: python

            status_json = package.services.status(service_id='service_id')
        """
        if service_id is None:
            if service_name is None:
                raise exceptions.PlatformException(error='400',
                                                   message='must input "service_name" or "service_id" to get status')
            service = self.get(service_name=service_name)
            service_id = service.id
        # request
        success, response = self._client_api.gen_request(req_type="get",
                                                         path="/services/{}/status".format(service_id))
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/services/{id}/stop', method='post')
    def pause(self,
              service_name: str = None,
              service_id: str = None,
              force: bool = False):
        """
        Pause service.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        You must provide at least ONE of the following params: service_id, service_name

        :param str service_name: service name
        :param str service_id: service id
        :param bool force: optional - terminate old replicas immediately
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = package.services.pause(service_id='service_id')
        """
        if service_id is None:
            if service_name is None:
                raise exceptions.PlatformException(error='400',
                                                   message='must input "service_name" or "service_id" to pause service')
            service = self.get(service_name=service_name)
            service_id = service.id
        # request
        url = "/services/{}/stop".format(service_id)
        if force:
            url = '{}?force=true'
        success, response = self._client_api.gen_request(req_type="post",
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)
        return success

    def _notify(
            self,
            service_id: str,
            message: str,
            name: str,
            action: str = 'created',
            support: str = None,
            docs: str = None
    ):
        url = "/services/{}/notify".format(service_id)
        payload = {
            'action': action,
            'message': message,
            'notificationName': name
        }

        if support:
            payload['support'] = support

        if docs:
            payload['docs'] = docs

        success, response = self._client_api.gen_request(
            req_type="post",
            path=url,
            json_req=payload
        )
        if not success:
            raise exceptions.PlatformException(response)
        return success

    @_api_reference.add(path='/services/{id}/resume', method='post')
    def resume(self,
               service_name: str = None,
               service_id: str = None,
               force: bool = False):
        """
        Resume service.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        You must provide at least ONE of the following params: service_id, service_name.

        :param str service_name: service name
        :param str service_id: service id
        :param bool force: optional - terminate old replicas immediately
        :return: json of the service
        :rtype: dict

        **Example**:

        .. code-block:: python

            service_json = package.services.resume(service_id='service_id')
        """
        if service_id is None:
            if service_name is None:
                raise exceptions.PlatformException(error='400',
                                                   message='must input "service_name" or "service_id" to resume')
            service = self.get(service_name=service_name)
            service_id = service.id
        # request
        url = "/services/{}/resume".format(service_id)
        if force:
            url = '{}?force=true'
        success, response = self._client_api.gen_request(req_type="post",
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def _get_bot_email(self, bot=None):

        if bot is None:
            project = self._project
            if project is None and self._project_id is not None:
                project = repositories.Projects(client_api=self._client_api).get(project_id=self._project_id)

            if project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Need project entity or bot to perform this action')
            bots = project.bots.list()
            if len(bots) == 0:
                logger.info('Bot not found for project. Creating a default bot')
                bot = project.bots.create(name='default')
            else:
                bot = bots[0]
                if len(bots) > 1:
                    logger.debug('More than one bot users. Choosing first. email: {}'.format(bots[0].email))

        if isinstance(bot, str):
            bot_email = bot
        elif isinstance(bot, entities.Bot) or isinstance(bot, entities.User):
            bot_email = bot.email
        else:
            raise ValueError('input "bot" must be a str or a Bot type, got: {}'.format(type(bot)))

        return bot_email

    @staticmethod
    def _parse_init_input(init_input):
        if not isinstance(init_input, dict):
            if init_input is None:
                init_input = dict()
            else:
                init_params = dict()
                if not isinstance(init_input, list):
                    init_input = [init_input]
                for param in init_input:
                    if isinstance(param, entities.FunctionIO):
                        init_params.update(param.to_json(resource='service'))
                    else:
                        raise exceptions.PlatformException('400', 'Unknown type of init params')
                init_input = init_params

        return init_input

    def name_validation(self, name: str):
        """
        Validation service name.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str name: service name

        **Example**:

        .. code-block:: python

            package.services.name_validation(name='name')
        """
        url = '/piper-misc/naming/services/{}'.format(name)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

    def _create(self,
                service_name: str = None,
                package: entities.Package = None,
                module_name: str = None,
                bot: Union[entities.Bot, str] = None,
                revision: str or int = None,
                init_input: Union[List[entities.FunctionIO], entities.FunctionIO, dict] = None,
                runtime: Union[entities.KubernetesRuntime, dict] = None,
                pod_type: entities.InstanceCatalog = None,
                project_id: str = None,
                sdk_version: str = None,
                agent_versions: dict = None,
                verify: bool = True,
                driver_id: str = None,
                run_execution_as_process: bool = None,
                execution_timeout: int = None,
                drain_time: int = None,
                on_reset: str = None,
                max_attempts: int = None,
                secrets=None,
                **kwargs
                ) -> entities.Service:
        """
        Create service entity.


        :param str service_name: service name
        :param dtlpy.entities.package.Package package: package entity
        :param str module_name: module name
        :param str bot: bot email
        :param str revision: package revision - default=latest
        :param init_input: config to run at startup
        :param dict runtime: runtime resources
        :param str pod_type: pod type dl.InstanceCatalog
        :param str project_id: project id
        :param str sdk_version:  - optional - string - sdk version
        :param dict agent_versions: - dictionary - - optional -versions of sdk, agent runner and agent proxy
        :param bool verify: verify the inputs
        :param str driver_id: driver id
        :param bool run_execution_as_process: run execution as process
        :param int execution_timeout: execution timeout
        :param int drain_time: drain time
        :param str on_reset: on reset
        :param int max_attempts: Maximum execution retries in-case of a service reset
        :param bool force: optional - terminate old replicas immediately
        :param list secrets: list of the integrations ids
        :param kwargs:
        :return: Service object
        :rtype: dtlpy.entities.service.Service
        """
        if package is None:
            if self._package is None:
                raise exceptions.PlatformException('400', 'Please provide param package')
            package = self._package

        if verify is not None:
            logger.warning('verify attribute has been deprecated and will be ignored')

        is_global = kwargs.get('is_global', None)
        jwt_forward = kwargs.get('jwt_forward', None)

        if is_global is not None or jwt_forward is not None:
            logger.warning(
                'Params jwt_forward and is_global are restricted to superuser. '
                'If you are not a superuser this action will not work'
            )

        service_config = dict()
        if package is not None and package.service_config is not None:
            service_config = package.service_config

        if agent_versions is None:
            if sdk_version is None:
                sdk_version = service_config.get('versions', dict()).get('dtlpy', __version__)
            agent_versions = {
                "dtlpy": sdk_version
            }

        if project_id is None:
            if self._project is None and self._project_id is None:
                raise exceptions.PlatformException('400', 'Please provide project id')
            elif self._project_id is not None:
                project_id = self._project_id
            elif self._project is not None:
                project_id = self._project.id

        if service_name is None:
            service_name = 'default-service'

        # payload
        payload = {
            'name': service_name,
            'projectId': project_id,
            'packageId': package.id,
            'initParams': self._parse_init_input(init_input=init_input),
            'botUserName': self._get_bot_email(bot=bot),
            'versions': agent_versions,
            'packageRevision': revision if revision is not None else package.version,
            'driverId': driver_id,
        }

        if secrets is not None:
            if not isinstance(secrets, list):
                secrets = [secrets]
            payload['secrets'] = secrets

        if runtime is not None:
            if isinstance(runtime, entities.KubernetesRuntime):
                runtime = runtime.to_json()

        if pod_type is not None:
            if runtime is None:
                runtime = {'podType': pod_type}
            else:
                runtime['podType'] = pod_type

        if runtime is not None:
            payload['runtime'] = runtime

        if module_name is not None:
            payload['moduleName'] = module_name

        if is_global is not None:
            payload['global'] = is_global

        if max_attempts is not None:
            payload['maxAttempts'] = max_attempts

        if jwt_forward is not None:
            payload['useUserJwt'] = jwt_forward

        if run_execution_as_process is not None:
            payload['runExecutionAsProcess'] = run_execution_as_process

        if drain_time is not None:
            payload['drainTime'] = drain_time

        if on_reset is not None:
            payload['onReset'] = on_reset

        if execution_timeout is not None:
            payload['executionTimeout'] = execution_timeout

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path='/services',
            json_req=payload
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Service.from_json(
            _json=response.json(),
            client_api=self._client_api,
            package=package,
            project=self._project
        )

    @_api_reference.add(path='/services/{id}', method='delete')
    def delete(self, service_name: str = None, service_id: str = None):
        """
        Delete Service object

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        You must provide at least ONE of the following params: service_id, service_name.

        :param str service_name: by name
        :param str service_id: by id
        :return: True
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = package.services.delete(service_id='service_id')
        """
        # get bby name
        if service_id is None:
            if service_name is None:
                raise exceptions.PlatformException('400', 'Must provide either service id or service name')
            else:
                service_id = self.get(service_name=service_name).id

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/services/{}".format(service_id)
        )
        if not success:
            raise exceptions.PlatformException(response)
        return True

    @_api_reference.add(path='/services/{id}', method='patch')
    def update(self, service: entities.Service, force: bool = False) -> entities.Service:
        """
        Update service changes to platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.service.Service service: Service entity
        :param bool force: optional - terminate old replicas immediately
        :return: Service entity
        :rtype: dtlpy.entities.service.Service

        **Example**:

        .. code-block:: python

            service = package.services.update(service='service_entity')
        """
        assert isinstance(service, entities.Service)

        # payload
        payload = service.to_json()

        # request
        url = '/services/{}'.format(service.id)
        if force:
            url = '{}?force=true'.format(url)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url,
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        if self._package is not None:
            package = self._package
        else:
            package = service._package

        return entities.Service.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          package=package,
                                          project=self._project)

    def activate_slots(
            self,
            service: entities.Service,
            project_id: str = None,
            task_id: str = None,
            dataset_id: str = None,
            org_id: str = None,
            user_email: str = None,
            slots: List[entities.PackageSlot] = None,
            role=None,
            prevent_override: bool = True,
            visible: bool = True,
            icon: str = 'fas fa-magic',
            **kwargs
    ):
        """
        Activate service slots (creates buttons in the UI that activate services).

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.service.Service service: service entity
        :param str project_id: project id
        :param str task_id: task id
        :param str dataset_id: dataset id
        :param str org_id: org id
        :param str user_email: user email
        :param list slots: list of entities.PackageSlot
        :param str role: user role MemberOrgRole.ADMIN, MemberOrgRole.owner, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :param bool prevent_override: True to prevent override
        :param bool visible: visible
        :param str icon: icon
        :param kwargs: all additional arguments
        :return: list of user setting for activated slots
        :rtype: list

        **Example**:

        .. code-block:: python

            setting = package.services.activate_slots(service='service_entity',
                                            project_id='project_id',
                                            slots=List[entities.PackageSlot],
                                            icon='fas fa-magic')
        """
        package = service.package
        if not isinstance(package.slots, list) or len(package.slots) == 0:
            raise exceptions.PlatformException('400', "Service's package has no slots")

        if kwargs.get('is_global', False):
            project_id = '*'
            scope_ids = [project_id]
        else:
            scope_ids = [s_id for s_id in [project_id, task_id, org_id, dataset_id, user_email] if s_id is not None]
            if len(scope_ids) == 0:
                raise exceptions.PlatformException('400', "Must provide scope resource ID")

        settings = list()

        if role is None:
            role = entities.Role.ALL

        if not slots:
            slots = [s.to_json() for s in service.package.slots]
        elif isinstance(slots, list) and isinstance(slots[0], entities.PackageSlot):
            slots = [s.to_json() for s in slots]
        else:
            raise exceptions.PlatformException('400', "Slots param must be a list of PackageSlot objects")

        for scope_id in scope_ids:

            if kwargs.get('is_global', False):
                scope_type = entities.PlatformEntityType.DATALOOP
            elif scope_id == project_id:
                scope_type = entities.PlatformEntityType.PROJECT
            elif scope_id == task_id:
                scope_type = entities.PlatformEntityType.TASK
            elif scope_id == dataset_id:
                scope_type = entities.PlatformEntityType.DATASET
            elif scope_id == user_email:
                scope_type = entities.PlatformEntityType.USER
            elif scope_id == org_id:
                scope_type = entities.PlatformEntityType.ORG
            else:
                raise exceptions.PlatformException('400', "Unknown resource id")

            setting = entities.Setting(
                default_value=True,
                value=True,
                inputs=None,
                name=service.name,
                value_type=entities.SettingsValueTypes.BOOLEAN,
                scope=entities.SettingScope(
                    type=scope_type,
                    id=scope_id,
                    role=role,
                    prevent_override=prevent_override,
                    visible=visible
                ),
                metadata={
                    'serviceId': service.id,
                    'serviceName': service.name,
                    'projectId': service.project_id,
                    'slots': slots
                },
                description=service.name,
                icon=icon,
                section_name=entities.SettingsSectionNames.APPLICATIONS,
                sub_section_name=None,
                hint=None
            )

            try:
                settings.append(self._settings.create(setting=setting))
            except exceptions.BadRequest as err:
                if 'settings already exist' in err.message:
                    old_setting = self._settings.get(setting_name=setting.name)
                    setting.id = old_setting.id
                    settings.append(self._settings.update(setting=setting))
                else:
                    raise err

        return settings

    @_api_reference.add(path='/services/logs', method='post')
    def log(self,
            service,
            size=100,
            checkpoint=None,
            start=None,
            end=None,
            follow=False,
            text=None,
            execution_id=None,
            function_name=None,
            replica_id=None,
            system=False,
            view=True,
            until_completed=True,
            log_level='DEBUG',
            model_id: str = None,
            model_operation: str = None,
            project_id: str = None
            ):
        """
        Get service logs.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.service.Service service: service object
        :param int size: size
        :param dict checkpoint: the information from the lst point checked in the service
        :param str start: iso format time
        :param str end: iso format time
        :param bool follow: if true, keep stream future logs
        :param str text: text
        :param str execution_id: execution id
        :param str function_name: function name
        :param str replica_id: replica id
        :param bool system: system
        :param bool view: if true, print out all the logs
        :param bool until_completed: wait until completed
        :param str log_level: the log level to display dl.LoggingLevel
        :param str model_id: model id
        :param str model_operation: model operation action
        :param str project_id: project id
        :return: ServiceLog entity
        :rtype: ServiceLog

        **Example**:

        .. code-block:: python

            service_logs = package.services.log(service='service_entity')
        """
        if not isinstance(service, entities.Service) and model_id is None:
            raise exceptions.PlatformException('400', 'Must provide service or model_id')
        if isinstance(log_level, str):
            log_level = log_level.upper()

        payload = {
            'direction': 'asc',
            'follow': follow,
            'system': system,
            'logLevel': log_level
        }

        if service is not None:
            payload['serviceId'] = service.id

        if size is not None:
            payload['size'] = size

        if execution_id is not None:
            payload['executionId'] = [execution_id]

        if function_name is not None:
            payload['functionName'] = function_name

        if text is not None:
            payload['text'] = text

        if replica_id is not None:
            payload['replicaId'] = replica_id

        if checkpoint is not None:
            payload['checkpoint'] = checkpoint

        if start is not None:
            payload['start'] = start
        else:
            payload['start'] = datetime.datetime(datetime.date.today().year,
                                                 datetime.date.today().month,
                                                 datetime.date.today().day,
                                                 0,
                                                 0,
                                                 0).isoformat()

        if end is not None:
            payload['end'] = end

        if model_id is not None:
            payload['modelId'] = model_id

        if model_operation is not None:
            payload['modelOperation'] = model_operation

        if project_id is not None:
            payload['projectId'] = project_id

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/services/logs',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        log = ServiceLog(_json=response.json(),
                         service=service,
                         services=self,
                         start=payload['start'],
                         follow=follow,
                         execution_id=execution_id,
                         function_name=function_name,
                         replica_id=replica_id,
                         system=system,
                         model_id=model_id,
                         model_operation=model_operation,
                         project_id=project_id)

        if view:
            log.view(until_completed=until_completed)
        else:
            return log

    def execute(self,
                service: entities.Service = None,
                service_id: str = None,
                service_name: str = None,
                sync: bool = False,
                function_name: str = None,
                stream_logs: bool = False,
                execution_input=None,
                resource=None,
                item_id=None,
                dataset_id=None,
                annotation_id=None,
                project_id=None,
                ) -> entities.Execution:
        """
        Execute a function on an existing service.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.service.Service service:  service entity
        :param str service_id:  service id
        :param str service_name: service name
        :param bool sync: wait for function to end
        :param str function_name: function name to run
        :param bool stream_logs: prints logs of the new execution. only works with sync=True
        :param execution_input: input dictionary or list of FunctionIO entities
        :param str resource: dl.PackageInputType - input type.
        :param str item_id: str - optional - input to function
        :param str dataset_id: str - optional - input to function
        :param str annotation_id: str - optional - input to function
        :param str project_id: str - resource's project
        :return: entities.Execution
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            execution = package.services.execute(service='service_entity',
                                    function_name='run',
                                    item_id='item_id',
                                    project_id='project_id')
        """
        if service is None:
            service = self.get(service_id=service_id, service_name=service_name)
        execution = repositories.Executions(service=service,
                                            client_api=self._client_api,
                                            project=self._project).create(service_id=service.id,
                                                                          sync=sync,
                                                                          execution_input=execution_input,
                                                                          function_name=function_name,
                                                                          resource=resource,
                                                                          item_id=item_id,
                                                                          dataset_id=dataset_id,
                                                                          annotation_id=annotation_id,
                                                                          project_id=project_id,
                                                                          stream_logs=stream_logs)
        return execution

    @_api_reference.add(path='/services', method='post')
    def deploy(self,
               service_name: str = None,
               package: entities.Package = None,
               bot: Union[entities.Bot, str] = None,
               revision: str or int = None,
               init_input: Union[List[entities.FunctionIO], entities.FunctionIO, dict] = None,
               runtime: Union[entities.KubernetesRuntime, dict] = None,
               pod_type: entities.InstanceCatalog = None,
               sdk_version: str = None,
               agent_versions: dict = None,
               verify: bool = True,
               checkout: bool = False,
               module_name: str = None,
               project_id: str = None,
               driver_id: str = None,
               func: Callable = None,
               run_execution_as_process: bool = None,
               execution_timeout: int = None,
               drain_time: int = None,
               max_attempts: int = None,
               on_reset: str = None,
               force: bool = False,
               secrets: list = None,
               **kwargs) -> entities.Service:
        """
        Deploy service.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param str service_name: name
        :param dtlpy.entities.package.Package package: package entity
        :param str bot: bot email
        :param str revision: package revision of version
        :param init_input: config to run at startup
        :param dict runtime: runtime resources
        :param str pod_type: pod type dl.InstanceCatalog
        :param str sdk_version:  - optional - string - sdk version
        :param str agent_versions: - dictionary - - optional -versions of sdk
        :param bool verify: if true, verify the inputs
        :param bool checkout: if true, checkout (switch) to service
        :param str module_name: module name
        :param str project_id: project id
        :param str driver_id: driver id
        :param Callable func: function to deploy
        :param bool run_execution_as_process: if true, run execution as process
        :param int execution_timeout: execution timeout in seconds
        :param int drain_time: drain time in seconds
        :param int max_attempts: maximum execution retries in-case of a service reset
        :param str on_reset: what happens on reset
        :param bool force: optional - if true, terminate old replicas immediately
        :param list secrets: list of the integrations ids
        :param kwargs: list of additional arguments
        :return: Service object
        :rtype: dtlpy.entities.service.Service

        **Example**:

        .. code-block:: python

            service = package.services.deploy(service_name=package_name,
                                    execution_timeout=3 * 60 * 60,
                                    module_name=module.name,
                                    runtime=dl.KubernetesRuntime(
                                        concurrency=10,
                                        pod_type=dl.InstanceCatalog.REGULAR_S,
                                        autoscaler=dl.KubernetesRabbitmqAutoscaler(
                                            min_replicas=1,
                                            max_replicas=20,
                                            queue_length=20
                                        )
                                    )
                                )
        """
        package = package if package is not None else self._package
        if service_name is None:
            get_name = False
            if package is not None and package.service_config is not None and 'name' in package.service_config:
                service_name = package.service_config['name']
                get_name = True
            else:
                if package is not None:
                    service_name = package.name
                else:
                    service_name = 'default-service'
            if not get_name:
                logger.warning('service_name not provided, using: {} by default'.format(service_name))

        if isinstance(revision, int):
            logger.warning('Deprecation Warning - Package/service versions have been refactored'
                           'The version you provided has type: int, it will be converted to: 1.0.{}'
                           'Next time use a 3-level semver for package/service versions'.format(revision))

        if func is not None:
            package = self.__deploy_function(name=service_name, project=self._project, func=func)

        if init_input is not None and not isinstance(init_input, dict):
            if not isinstance(init_input, list):
                init_input = [init_input]

            if len(init_input) > 0 and isinstance(init_input[0], entities.FunctionIO):
                params = dict()
                for i_param, param in enumerate(init_input):
                    params[param.name] = param.value
                init_input = params
            elif len(init_input) == 0:
                init_input = None
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='Unknown init_input type. expecting list or dict, got: {}'.format(type(init_input))
                )

        if project_id is None:
            if self._project is not None:
                project_id = self._project.id
            else:
                project_id = self._project_id

        filters = entities.Filters(resource=entities.FiltersResource.SERVICE)
        filters.add(field='name', values=service_name)
        if project_id is not None:
            filters.add(field='projectId', values=project_id)
        services = self.list(filters=filters)
        if services.items_count > 1:
            raise exceptions.PlatformException('400',
                                               'More than 1 service by this name are associated with this user. '
                                               'Please provide project_id')
        elif services.items_count > 0:
            service = services.items[0]
            if runtime is not None:
                service.runtime = runtime
            if init_input is not None:
                service.init_input = init_input
            if revision is not None:
                service.package_revision = revision
            if agent_versions is not None:
                service.versions = agent_versions
            elif sdk_version:
                service.versions = {'dtlpy': sdk_version}
            if driver_id is not None:
                service.driver_id = driver_id
            if secrets is not None:
                if not isinstance(secrets, list):
                    secrets = [secrets]
                service.secrets = secrets
            service = self.update(service=service, force=force)
        else:
            service = self._create(service_name=service_name,
                                   package=package,
                                   project_id=project_id,
                                   bot=bot,
                                   revision=revision,
                                   init_input=init_input,
                                   runtime=runtime,
                                   pod_type=pod_type,
                                   sdk_version=sdk_version,
                                   agent_versions=agent_versions,
                                   verify=verify,
                                   module_name=module_name,
                                   driver_id=driver_id,
                                   jwt_forward=kwargs.get('jwt_forward', None),
                                   is_global=kwargs.get('is_global', None),
                                   run_execution_as_process=run_execution_as_process,
                                   execution_timeout=execution_timeout,
                                   drain_time=drain_time,
                                   max_attempts=max_attempts,
                                   on_reset=on_reset,
                                   secrets=secrets
                                   )
        if checkout:
            self.checkout(service=service)
        return service

    @staticmethod
    def __get_import_string(imports: List[str]):
        import_string = ''
        if imports is not None:
            import_string = '\n'.join(imports)
        return import_string

    @staticmethod
    def __get_inputs(func):
        method = inspect.signature(func)
        params = list(method.parameters)
        inpts = list()
        inputs_types = {i.name.lower(): i.value for i in list(entities.PackageInputType)}
        for arg in params:
            if arg in inputs_types:
                inpt_type = inputs_types[arg]
            else:
                inpt_type = entities.PackageInputType.JSON
            inpts.append(entities.FunctionIO(type=inpt_type, name=arg))
        return inpts

    def __deploy_function(self,
                          name: str,
                          func: Callable,
                          project: entities.Project) -> entities.Package:
        package_dir = tempfile.mkdtemp()
        # imports_string = self.__get_import_string()
        imports_string = ''

        main_file = os.path.join(package_dir, entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT)
        with open(assets.paths.PARTIAL_MAIN_FILEPATH, 'r') as f:
            main_string = f.read()
        lines = inspect.getsourcelines(func)
        tabs_diff = lines[0][0].count('    ') - 1
        for line_index in range(len(lines[0])):
            line_tabs = lines[0][line_index].count('    ') - tabs_diff
            lines[0][line_index] = ('    ' * line_tabs) + lines[0][line_index].strip() + '\n'

        method_func_string = "".join(lines[0])

        with open(main_file, 'w') as f:
            f.write('{}\n{}\n    @staticmethod\n{}'.format(imports_string, main_string,
                                                           method_func_string))

        function = entities.PackageFunction(name=func.__name__, inputs=self.__get_inputs(func=func))
        module = entities.PackageModule(functions=[function],
                                        entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT)
        packages = repositories.Packages(client_api=self._client_api, project=project)
        return packages.push(src_path=package_dir,
                             package_name=name,
                             checkout=True,
                             modules=[module])

    def deploy_from_local_folder(self,
                                 cwd=None,
                                 service_file=None,
                                 bot=None,
                                 checkout=False,
                                 force=False
                                 ) -> entities.Service:
        """
        Deploy from local folder in local environment.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param str cwd: optional - package working directory. Default=cwd
        :param str service_file: optional - service file. Default=None
        :param str bot: bot
        :param checkout: checkout
        :param bool force: optional - terminate old replicas immediately
        :return: Service object
        :rtype: dtlpy.entities.service.Service

        **Example**:

        .. code-block:: python

            service = package.services.deploy_from_local_folder(cwd='file_path',
                                                      service_file='service_file')
        """
        # get cwd and service.json path
        if cwd is None:
            cwd = os.getcwd()
        if service_file is None:
            service_file = os.path.join(cwd, assets.paths.SERVICE_FILENAME)

        # load service json
        if os.path.isfile(service_file):
            with open(service_file, 'r') as f:
                service_json = json.load(f)
            service_triggers = service_json.get('triggers', list())
        else:
            raise exceptions.PlatformException(error='400',
                                               message='Could not find service.json in path: {}'.format(cwd))

        # get package
        package_name = service_json.get('packageName', None)
        packages = repositories.Packages(client_api=self._client_api, project=self._project)

        if package_name is None:
            package = packages.get()
        else:
            package = packages.get(package_name=package_name)

        name = service_json.get('name', None)
        revision = service_json.get('revision', package.version)
        init_input = service_json.get('initParams', dict())
        runtime = service_json.get('runtime', dict())
        sdk_version = service_json.get('version', None)
        agent_versions = service_json.get('versions', None)
        verify = service_json.get('verify', True)
        module_name = service_json.get('module_name', None)
        run_execution_as_process = service_json.get('run_execution_as_process', None)
        execution_timeout = service_json.get('execution_timeout', None)
        drain_time = service_json.get('drain_time', None)
        on_reset = service_json.get('on_reset', None)
        max_attempts = service_json.get('maxAttempts', None)

        service = self.deploy(bot=bot,
                              service_name=name,
                              package=package,
                              revision=revision,
                              runtime=runtime,
                              init_input=init_input,
                              sdk_version=sdk_version,
                              agent_versions=agent_versions,
                              verify=verify,
                              checkout=checkout,
                              run_execution_as_process=run_execution_as_process,
                              execution_timeout=execution_timeout,
                              drain_time=drain_time,
                              max_attempts=max_attempts,
                              on_reset=on_reset,
                              module_name=module_name,
                              force=force
                              )

        logger.info('Service was deployed successfully. Service id: {}'.format(service.id))

        if len(service_triggers) > 0:
            logger.info('Creating triggers...')
            triggers = repositories.Triggers(client_api=self._client_api, project=self._project)

            for trigger in service_triggers:
                name = trigger.get('name', None)
                filters = trigger.get('filter', dict())
                resource = trigger['resource']
                actions = trigger.get('actions', list())
                active = trigger.get('active', True)
                execution_mode = trigger.get('executionMode', None)
                function_name = trigger.get('function', None)

                trigger = triggers.create(service_id=service.id,
                                          name=name,
                                          filters=filters,
                                          resource=resource,
                                          actions=actions,
                                          active=active,
                                          execution_mode=execution_mode,
                                          function_name=function_name)

                logger.info('Trigger was created successfully. Service id: {}'.format(trigger.id))

        logging.info('Successfully deployed!')
        return service

    def __enable_cache(self,
                       url,
                       organization: entities.Organization,
                       pod_type=entities.PodType.SMALL):
        payload = {
            "org": {
                "name": organization.name,
                "id": organization.id
            },
            "runner": {
                "podType": pod_type  # small, medium, high
            }
        }

        return self._client_api.gen_request(req_type='post',
                                            path=url,
                                            json_req=payload)

    def __polling_wait(self, organization, pod_type, backoff_factor=0.1):
        fs_url_path = '/services/fs-cache?mode={}'.format('get')
        i = 1
        while True:
            success, response = self.__enable_cache(url=fs_url_path, organization=organization, pod_type=pod_type)
            if response.json().get('state', None) == 'READY':
                break
            sleep_time = min(backoff_factor * (2 ** (i - 1)), MAX_WAIT_TIME)
            logger.debug("Going to sleep {:.2f}[s]".format(sleep_time))
            time.sleep(sleep_time)
            i += 1
        return success

    def _cache_action(self,
                      organization: entities.Organization = None,
                      mode=entities.CacheAction.APPLY,
                      pod_type=entities.PodType.SMALL):
        """
        Add or remove Cache for the org

        **Prerequisites**: You must be an organization *owner*

        You must provide at least ONE of the following params: organization, organization_name, or organization_id.

        :param entities.Organization organization: Organization object
        :param str mode: dl.CacheAction.APPLY or dl.CacheAction.DESTROY
        :param entities.PodType pod_type:  dl.PodType.SMALL, dl.PodType.MEDIUM, dl.PodType.HIGH
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dl.organizations.enable_cache(organization='organization',
                                          mode=dl.CacheAction.APPLY)
        """
        if organization is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        fs_mode = mode if mode != entities.CacheAction.APPLY else '{}-filestore'.format(mode)
        apply_fs_url_path = '/services/fs-cache?mode={}'.format(fs_mode)
        apply_volume_url_path = '/services/fs-cache?mode={}'.format(mode)
        cache_url_path = '/services/cache?mode={}'.format(mode)

        success, response = self.__enable_cache(url=apply_fs_url_path, organization=organization, pod_type=pod_type)
        if not success:
            raise exceptions.PlatformException(response)

        if mode == entities.CacheAction.APPLY:
            self.__polling_wait(organization=organization, pod_type=pod_type)
            success, response = self.__enable_cache(url=apply_volume_url_path, organization=organization,
                                                    pod_type=pod_type)
            if not success:
                raise exceptions.PlatformException(response)

        success, response = self.__enable_cache(url=cache_url_path, organization=organization, pod_type=pod_type)
        if not success:
            raise exceptions.PlatformException(response)

        return True


class ServiceLog:
    """
    Service Log
    """

    def __init__(self,
                 _json: dict,
                 service: entities.Service,
                 services: Services,
                 start=None,
                 follow=None,
                 execution_id=None,
                 function_name=None,
                 replica_id=None,
                 system=False,
                 model_id=None,
                 model_operation=None,
                 project_id=None):

        self.logs = _json.get('logs', dict())
        self.checkpoint = _json.get('checkpoint', None)
        self.stop = _json.get('stop', False)
        self.service = service
        self.services = services
        self.start = start
        self.follow = follow
        self.execution_id = execution_id
        self.function_name = function_name
        self.replica_id = replica_id
        self.system = system
        self.model_id = model_id
        self.model_operation = model_operation
        self.project_id = project_id

    def get_next_log(self):
        log = self.services.log(service=self.service,
                                checkpoint=self.checkpoint,
                                start=self.start,
                                follow=self.follow,
                                execution_id=self.execution_id,
                                function_name=self.function_name,
                                replica_id=self.replica_id,
                                system=self.system,
                                view=False,
                                model_id=self.model_id,
                                model_operation=self.model_operation,
                                project_id=self.project_id)

        self.logs = log.logs
        self.checkpoint = log.checkpoint
        self.stop = log.stop

    def view(self, until_completed):
        """
        View logs

        :param until_completed:
        """
        try:
            for log in self:
                print(log)
                if until_completed and FUNCTION_END_LINE in log:
                    break
        except KeyboardInterrupt:
            return

    def __iter__(self):
        while not self.stop:
            for log in self.logs:
                yield '{}: {}'.format(log.get('timestamp', self.start), log.get('message', '').strip())
            self.get_next_log()
