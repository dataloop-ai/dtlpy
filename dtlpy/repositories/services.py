import datetime
import inspect
import logging
import json
import os
import tempfile
from typing import Union, List, Callable

from .. import miscellaneous, exceptions, entities, repositories, assets, ApiClient
from ..__version__ import version as __version__

logger = logging.getLogger(name=__name__)
FUNCTION_END_LINE = '[Done] Executing function.'


class Services:
    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 package: entities.Package = None,
                 project_id=None):
        self._client_api = client_api
        self._package = package
        self._project = project
        if project_id is None:
            if project is not None:
                project_id = project.id
        self._project_id = project_id

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

    def open_in_web(self, service=None, service_id=None, service_name=None):
        """
        :param service_name:
        :param service_id:
        :param service:
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

    def checkout(self, service: entities.Service = None, service_name=None, service_id=None):
        """
        Check-out a service
        :param service: Service entity
        :param service_name:
        :param service_id:
        :return:
        """
        if service is None:
            service = self.get(service_name=service_name, service_id=service_id)
        self._client_api.state_io.put('service', service.to_json())
        logger.info('Checked out to service {}'.format(service.name))

    ###########
    # methods #
    ###########
    def revisions(self, service: entities.Service = None, service_id=None):
        """
        Get service revisions history

        :param service: Package entity
        :param service_id: package id
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

    def get(self, service_name=None, service_id=None, checkout=False, fetch=None) -> entities.Service:
        """
        Get service

        :param checkout:
        :param service_name: optional - search by name
        :param service_id: optional - search by id
        :param checkout:
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Service object
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
                                                 package=self,
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

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project services
        :param filters:
        :return:
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

    def status(self, service_name=None, service_id=None):
        """

        :param service_name:
        :param service_id:
        :return:
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

    def pause(self, service_name=None, service_id=None, force=False):
        """

        :param service_name:
        :param service_id:
        :param force: optional - terminate old replicas immediately
        :return:
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

    def resume(self, service_name=None, service_id=None, force=False):
        """

        :param service_name:
        :param service_id:
        :param force: optional - terminate old replicas immediately
        :return:
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
        :param name:
        """
        url = '/piper-misc/naming/services/{}'.format(name)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

    def _create(self, service_name=None, package=None, module_name=None, bot=None, revision=None, init_input=None,
                runtime=None, pod_type=None, project_id=None, sdk_version=None, agent_versions=None, verify=True,
                driver_id=None, run_execution_as_process=None, execution_timeout=None, drain_time=None, on_reset=None,
                max_attempts=None, secrets=None, **kwargs) -> entities.Service:
        """
        Create service entity
        :param service_name:
        :param package:
        :param module_name:
        :param bot: bot user that weill run the package
        :param revision: optional - int - package revision - default=latest
        :param init_input:
        :param runtime:
        :param pod_type:
        :param project_id:
        :param sdk_version:
        :param agent_versions:
        :param verify:
        :param driver_id:
        :param run_execution_as_process:
        :param execution_timeout:
        :param drain_time:
        :param on_reset:
        :param max_attempts:
        :param secrets: list of the integrations ids
        :param kwargs:
        :return:
        """
        if package is None:
            if self._package is None:
                raise exceptions.PlatformException('400', 'Please provide param package')
            package = self._package

        if package is not None and package.service_config is not None:
            module_name, agent_versions, runtime, pod_type = self.set_service_config(module_name,
                                                                                     agent_versions,
                                                                                     runtime, pod_type,
                                                                                     package.service_config)
        is_global = kwargs.get('is_global', None)
        jwt_forward = kwargs.get('jwt_forward', None)
        if is_global is not None or jwt_forward is not None:
            logger.warning(
                'Params jwt_forward and is_global are restricted to superuser. '
                'If you are not a superuser this action will not work')

        if agent_versions is None:
            if sdk_version is None:
                sdk_version = __version__
            agent_versions = {
                "dtlpy": sdk_version,
                "verify": verify
            }

        if project_id is None:
            if self._project is None and self._project_id is None:
                raise exceptions.PlatformException('400', 'Please provide project id')
            elif self._project_id is not None:
                project_id = self._project_id
            elif self._project is not None:
                project_id = self._project.id

        if module_name is None:
            module_name = entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME
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
            'moduleName': module_name,
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
            payload['runtime'] = runtime
        else:
            payload['runtime'] = {'gpu': False,
                                  'numReplicas': 1}

        if pod_type is None:
            if 'gpu' in payload['runtime'] and payload['runtime']['gpu']:
                pod_type = 'gpu-k80-s'
            else:
                pod_type = 'regular-s'
        elif 'podType' not in payload['runtime'] and payload['runtime']['podType'] != pod_type:
            raise exceptions.PlatformException('400', 'Different pod_types given in param and in runtime.\n'
                                                      'pod_type param = {}\n'
                                                      'pod_type in runtime = {}'.format(pod_type,
                                                                                        payload['runtime']['podType']))

        if is_global is not None:
            payload['global'] = is_global

        if max_attempts is not None:
            payload['maxAttempts'] = max_attempts

        if jwt_forward is not None:
            payload['useUserJwt'] = jwt_forward

        if 'podType' not in payload['runtime']:
            payload['runtime']['podType'] = pod_type

        if run_execution_as_process is not None:
            payload['runExecutionAsProcess'] = run_execution_as_process

        if drain_time is not None:
            payload['drainTime'] = drain_time

        if on_reset is not None:
            payload['onReset'] = on_reset

        if execution_timeout is not None:
            payload['executionTimeout'] = execution_timeout

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/services',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Service.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          package=package,
                                          project=self._project)

    def delete(self, service_name=None, service_id=None):
        """
        Delete Service object
        :param service_name: by name
        :param service_id: by id
        :return: True
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

    def update(self, service: entities.Service, force=False) -> entities.Service:
        """
        Update Service changes to platform
        :param service: Service entity
        :param force: optional - terminate old replicas immediately
        :return: Service entity
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

    def log(self, service, size=None, checkpoint=None, start=None, end=None, follow=False, text=None,
            execution_id=None, function_name=None, replica_id=None, system=False, view=True, until_completed=True):
        """
        Get service logs

        :param service:
        :param size:
        :param checkpoint:
        :param start: iso format time
        :param end: iso format time
        :param follow: keep stream future logs
        :param text:
        :param execution_id:
        :param function_name:
        :param replica_id:
        :param system:
        :param view:
        :param until_completed:
        :return: Service entity
        """
        assert isinstance(service, entities.Service)

        payload = {
            'direction': 'asc',
            'follow': follow,
            'system': system
        }

        if size is not None:
            payload['size'] = size

        if execution_id is not None:
            payload['executionId'] = execution_id

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

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/services/{}/logs'.format(service.id),
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
                         system=system)

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
        service execute
        :param service:
        :param service_id:
        :param service_name:
        :param sync:
        :param function_name:
        :param stream_logs:
        :param execution_input:
        :param resource:
        :param item_id:
        :param dataset_id:
        :param annotation_id:
        :param project_id:
        :return entities.Execution:
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

    def set_service_config(self, module_name, agent_versions, runtime, pod_type, service_config):
        """
        set service defaults
        :param module_name:
        :param runtime:
        :param pod_type:
        :param agent_versions:
        :param service_config:
        :return:
        """
        if module_name is None:
            module_name = service_config.get('moduleName', None)
        if agent_versions is None:
            agent_versions = service_config.get('versions', None)
        if runtime is None:
            runtime = service_config.get('runtime', None)
        if pod_type is None:
            pod_type = service_config.get('podType', None)
        return module_name, agent_versions, runtime, pod_type

    def deploy(self,
               service_name: str = None,
               package: entities.Package = None,
               bot: Union[entities.Bot, str] = None,
               revision: str or int = None,
               init_input: Union[List[entities.FunctionIO], entities.FunctionIO, dict] = None,
               runtime: Union[entities.KubernetesRuntime, dict] = None,
               pod_type: str = None,
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
        Deploy service

        :param service_name: name
        :param package: package entity
        :param bot: bot email
        :param revision: version
        :param init_input: config to run at startup
        :param runtime: runtime resources
        :param pod_type:
        :param sdk_version:  - optional - string - sdk version
        :param agent_versions: - dictionary - - optional -versions of sdk, agent runner and agent proxy
        :param verify:
        :param checkout:
        :param module_name:
        :param project_id:
        :param driver_id:
        :param func:
        :param run_execution_as_process:
        :param execution_timeout:
        :param drain_time:
        :param max_attempts: Maximum execution retries in-case of a service reset
        :param on_reset:
        :param force: optional - terminate old replicas immediately
        :param secrets: list of the integrations ids
        :param kwargs:
        :return:
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
                    message='Unknown init_input type. expecting list or dict, got: {}'.format(type(init_input)))

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
        inputs_types = [input_type.lower() for input_type in dir(entities.PackageInputType) if
                        not input_type.startswith('_') and input_type != 'JSON']
        for arg in params:
            if arg in inputs_types:
                inpt_type = arg.capitalize()
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
        method_func_string = "".join(lines[0])

        with open(main_file, 'w') as f:
            f.write('{}\n{}\n    @staticmethod\n    {}'.format(imports_string, main_string,
                                                               method_func_string.replace('\n', '\n    ')))

        function = entities.PackageFunction(name=func.__name__, inputs=self.__get_inputs(func=func))
        module = entities.PackageModule(functions=[function],
                                        entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT)
        packages = repositories.Packages(client_api=self._client_api, project=project)
        return packages.push(src_path=package_dir,
                             package_name=name,
                             checkout=True,
                             modules=[module])

    def deploy_from_local_folder(self, cwd=None, service_file=None, bot=None, checkout=False,
                                 force=False) -> entities.Service:
        """
        Deploy from local folder
        :param cwd: optional - package working directory. Default=cwd
        :param service_file: optional - service file. Default=None
        :param bot:
        :param checkout:
        :param force: optional - terminate old replicas immediately
        :return:
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

    def deploy_pipeline(self, service_json_path=None, project=None, bot=None, force=False):
        """
        Deploy pipeline
        :param service_json_path:
        :param project:
        :param bot:
        :param force:
        :return: True
        """
        # project
        if project is None:
            project = self._project

        # get service file
        if service_json_path is None:
            service_json_path = os.getcwd()

        if not service_json_path.endswith('.json'):
            service_json_path = os.path.join(service_json_path, 'service.json')
            if not os.path.isfile(service_json_path):
                raise exceptions.PlatformException('404', 'File not exist: {}'.format(service_json_path))

        # get existing project's services and triggers
        project_triggers = {trigger.name: trigger for trigger in project.triggers.list()}
        project_services = {service.name: service for service in project.services.list()}
        project_packages = {package.name: package for package in project.packages.list()}

        # load file
        with open(service_json_path, 'r') as f:
            service_json = json.load(f)

        # build
        for service_input in service_json:
            # get package
            if service_input['package'] in project_packages:
                package = project_packages[service_input['package']]
            else:
                raise exceptions.PlatformException('404', 'Package not found, package name: {}'.format(
                    service_input['package']))

            sdk_version = service_json.get('version', None)
            agent_versions = service_json.get('versions', None)
            verify = service_json.get('verify', True)
            runtime = service_input.get('runtime', None)
            init_input = service_input.get('initParams', None)
            module_name = service_input.get('module_name', None)
            driver_id = service_input.get('driverId', None)
            run_execution_as_process = service_json.get('run_execution_as_process', None)
            execution_timeout = service_json.get('execution_timeout', None)
            drain_time = service_json.get('drain_time', None)
            max_attempts = service_json.get('maxAttempts', None)
            on_reset = service_json.get('on_reset', None)
            # create or update service
            if service_input['name'] in project_services:
                service = project_services[service_input['name']]
                service.runtime = runtime
                service.init_input = init_input
                service.version = sdk_version
                service.versions = agent_versions
                service.verify = verify
                service.max_attempts = max_attempts
                service.driver_id = driver_id
                service = project.services.update(service=service, force=force)
                project_services[service.name] = service

            else:
                service = self._create(package=package,
                                       bot=bot,
                                       service_name=service_input['name'],
                                       runtime=runtime,
                                       init_input=init_input,
                                       agent_versions=agent_versions,
                                       sdk_version=sdk_version,
                                       max_attempts=max_attempts,
                                       verify=verify,
                                       module_name=module_name,
                                       run_execution_as_process=run_execution_as_process,
                                       execution_timeout=execution_timeout,
                                       drain_time=drain_time,
                                       on_reset=on_reset,
                                       driver_id=driver_id)
                project_services[service.name] = service

            service_triggers = {trigger: project_triggers[trigger] for trigger in project_triggers if
                                project_triggers[trigger].service_id == service.id}

            # create or update triggers
            if 'triggers' in service_input:
                for trigger_input in service_input['triggers']:
                    if trigger_input['name'] in service_triggers:
                        trigger = project_triggers[trigger_input['name']]
                        trigger.resource = trigger_input.get('resource', trigger.resource)
                        trigger.active = trigger_input.get('active', trigger.active)
                        trigger.actions = trigger_input.get('actions', trigger.actions)
                        trigger.filters = trigger_input.get('filters', trigger.filters)
                        trigger.execution_mode = trigger_input.get('executionMode', trigger.execution_mode)
                        trigger.function_name = trigger_input.get('function', None)
                        trigger = trigger.update()
                        project_triggers[trigger.name] = trigger
                    else:
                        trigger = project.triggers.create(service_ids=[service.id],
                                                          resource=trigger_input.get('resource', None),
                                                          active=trigger_input.get('active', None),
                                                          actions=trigger_input.get('actions', None),
                                                          filters=trigger_input.get('filters', None),
                                                          function_name=trigger_input.get('function', None),
                                                          execution_mode=trigger_input.get('executionMode', None))
                        project_triggers[trigger.name] = trigger

        print('File deployed successfully!')
        return True

    def tear_down(self, service_json_path=None, project=None):
        """
        Tear down a pipeline
        :param service_json_path:
        :param project:
        :return:
        """
        # project
        if project is None:
            project = self._project

        # get service file
        if service_json_path is None:
            service_json_path = os.getcwd()

        if not service_json_path.endswith('.json'):
            service_json_path = os.path.join(service_json_path, 'service.json')
            if not os.path.isfile(service_json_path):
                raise exceptions.PlatformException('404', 'File not exist: {}'.format(service_json_path))

        # get existing project's services and triggers
        project_triggers = {trigger.name: trigger for trigger in project.triggers.list()}
        project_services = {service.name: service for service in project.services.list()}

        with open(service_json_path, 'r') as f:
            service_json = json.load(f)

        # tear down
        for service_input in service_json:
            # delete service
            if service_input['name'] in project_services:
                service = project_services[service_input['name']]
                service.delete()

            # delete triggers
            if 'triggers' in service_input:
                for trigger_input in service_input['triggers']:
                    if trigger_input['name'] in project_triggers:
                        trigger = project_triggers[trigger_input['name']]
                        trigger.delete()

        print('File torn down successfully!')
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
                 system=False):

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

    def get_next_log(self):
        log = self.services.log(service=self.service,
                                checkpoint=self.checkpoint,
                                start=self.start,
                                follow=self.follow,
                                execution_id=self.execution_id,
                                function_name=self.function_name,
                                replica_id=self.replica_id,
                                system=self.system,
                                view=False)

        self.logs = log.logs
        self.checkpoint = log.checkpoint
        self.stop = log.stop

    def view(self, until_completed):
        """
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
