from collections import namedtuple
from enum import Enum
import traceback
import logging
from typing import List
import attr
from .. import services, repositories, entities

logger = logging.getLogger(name='dtlpy')


class OnResetAction(str, Enum):
    RERUN = 'rerun'
    FAILED = 'failed'


@attr.s
class Service(entities.BaseEntity):
    """
    Service object
    """
    # platform
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    creator = attr.ib()
    version = attr.ib()

    package_id = attr.ib()
    package_revision = attr.ib()

    bot = attr.ib()
    use_user_jwt = attr.ib(repr=False)
    init_input = attr.ib()
    versions = attr.ib(repr=False)
    module_name = attr.ib()
    name = attr.ib()
    url = attr.ib()
    id = attr.ib()
    active = attr.ib()
    driver_id = attr.ib(repr=False)
    secrets = attr.ib(repr=False)

    # name change
    runtime = attr.ib(repr=False)
    queue_length_limit = attr.ib()
    run_execution_as_process = attr.ib(type=bool)
    execution_timeout = attr.ib()
    drain_time = attr.ib()
    on_reset = attr.ib(type=OnResetAction)
    project_id = attr.ib()
    is_global = attr.ib()
    max_attempts = attr.ib()

    # SDK
    _package = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _revisions = attr.ib(default=None, repr=False)
    # repositories
    _project = attr.ib(default=None, repr=False)
    _repositories = attr.ib(repr=False)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @staticmethod
    def _protected_from_json(_json: dict, client_api: services.ApiClient, package=None, project=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity
        :param package:
        :param project: project entity
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        try:
            service = Service.from_json(_json=_json,
                                        client_api=client_api,
                                        package=package,
                                        project=project,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            service = traceback.format_exc()
            status = False
        return status, service

    @classmethod
    def from_json(cls, _json: dict, client_api: services.ApiClient, package=None, project=None, is_fetched=True):
        """
        Build a service entity object from a json

        :param dict _json: platform json
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.package.Package package: package entity
        :param dtlpy.entities.project.Project project: project entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: service object
        :rtype: dtlpy.entities.service.Service
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Service has been fetched from a project that is not belong to it')
                project = None

        if package is not None:
            if package.id != _json.get('packageId', None):
                logger.warning('Service has been fetched from a package that is not belong to it')
                package = None

        versions = _json.get('versions', dict())
        runtime = _json.get("runtime", None)
        if runtime:
            runtime = KubernetesRuntime(**runtime)

        inst = cls(
            package_revision=_json.get("packageRevision", None),
            bot=_json.get("botUserName", None),
            use_user_jwt=_json.get("useUserJwt", False),
            created_at=_json.get("createdAt", None),
            updated_at=_json.get("updatedAt", None),
            project_id=_json.get('projectId', None),
            package_id=_json.get('packageId', None),
            driver_id=_json.get('driverId', None),
            max_attempts=_json.get('maxAttempts', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            revisions=_json.get('revisions', None),
            queue_length_limit=_json.get('queueLengthLimit', None),
            active=_json.get('active', None),
            runtime=runtime,
            is_global=_json.get("global", False),
            init_input=_json.get("initParams", dict()),
            module_name=_json.get("moduleName", None),
            run_execution_as_process=_json.get('runExecutionAsProcess', False),
            execution_timeout=_json.get('executionTimeout', 60 * 60),
            drain_time=_json.get('drainTime', 60 * 10),
            on_reset=_json.get('onReset', OnResetAction.FAILED),
            name=_json.get("name", None),
            url=_json.get("url", None),
            id=_json.get("id", None),
            versions=versions,
            client_api=client_api,
            package=package,
            project=project,
            secrets=("secrets", None)
        )
        inst.is_fetched = is_fetched
        return inst

    ############
    # Entities #
    ############
    @property
    def revisions(self):
        if self._revisions is None:
            self._revisions = self.services.revisions(service=self)
        return self._revisions

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/services/{}/main".format(self.project.id, self.id))

    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def package(self):
        if self._package is None:
            self._package = repositories.Packages(client_api=self._client_api).get(package_id=self.package_id,
                                                                                   fetch=None)
        assert isinstance(self._package, entities.Package)
        return self._package

    @property
    def execution_url(self):
        return 'CURL -X POST' \
               '\nauthorization: Bearer <token>' \
               '\nContent-Type: application/json" -d {' \
               '\n"input": {<input json>}, ' \
               '"projectId": "{<project_id>}", ' \
               '"functionName": "<function_name>"}'

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['executions', 'services', 'triggers'])

        if self._package is None:
            services_repo = repositories.Services(client_api=self._client_api,
                                                  package=self._package,
                                                  project=self._project)
        else:
            services_repo = self._package.services

        triggers = repositories.Triggers(client_api=self._client_api,
                                         project=self._project,
                                         service=self)

        r = reps(executions=repositories.Executions(client_api=self._client_api, service=self),
                 services=services_repo, triggers=triggers)
        return r

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    ###########
    # methods #
    ###########
    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Service)._project,
                attr.fields(Service)._package,
                attr.fields(Service)._revisions,
                attr.fields(Service)._client_api,
                attr.fields(Service)._repositories,
                attr.fields(Service).project_id,
                attr.fields(Service).init_input,
                attr.fields(Service).module_name,
                attr.fields(Service).bot,
                attr.fields(Service).package_id,
                attr.fields(Service).is_global,
                attr.fields(Service).use_user_jwt,
                attr.fields(Service).package_revision,
                attr.fields(Service).driver_id,
                attr.fields(Service).run_execution_as_process,
                attr.fields(Service).execution_timeout,
                attr.fields(Service).drain_time,
                attr.fields(Service).runtime,
                attr.fields(Service).queue_length_limit,
                attr.fields(Service).max_attempts,
                attr.fields(Service).on_reset,
                attr.fields(Service).secrets,
                attr.fields(Service).created_at,
                attr.fields(Service).updated_at,
            )
        )

        _json['projectId'] = self.project_id
        _json['packageId'] = self.package_id
        _json['initParams'] = self.init_input
        _json['moduleName'] = self.module_name
        _json['botUserName'] = self.bot
        _json['useUserJwt'] = self.use_user_jwt
        _json['global'] = self.is_global
        _json['driverId'] = self.driver_id
        _json['packageRevision'] = self.package_revision
        _json['runExecutionAsProcess'] = self.run_execution_as_process
        _json['executionTimeout'] = self.execution_timeout
        _json['drainTime'] = self.drain_time
        _json['onReset'] = self.on_reset
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at

        if self.max_attempts is not None:
            _json['maxAttempts'] = self.max_attempts

        if self.is_global is not None:
            _json['global'] = self.is_global

        if self.runtime:
            _json['runtime'] = self.runtime if isinstance(self.runtime, dict) else self.runtime.to_json()

        if self.queue_length_limit is not None:
            _json['queueLengthLimit'] = self.queue_length_limit

        return _json

    def update(self, force=False):
        """
        Update Service changes to platform

        :param bool force: force update
        :return: Service entity
        :rtype: dtlpy.entities.service.Service
        """
        return self.services.update(service=self, force=force)

    def delete(self):
        """
        Delete Service object

        :return: True
        :rtype: bool
        """
        return self.services.delete(service_id=self.id)

    def status(self):
        """
        Get Service status

        :return: status json
        :rtype: dict
        """
        return self.services.status(service_id=self.id)

    def log(self, size=None, checkpoint=None, start=None, end=None, follow=False, text=None,
            execution_id=None, function_name=None, replica_id=None, system=False, view=True, until_completed=True):
        """
        Get service logs

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
        :return: ServiceLog entity
        :rtype: ServiceLog

        **Example**:

        .. code-block:: python

            service.log()
        """
        return self.services.log(service=self,
                                 size=size,
                                 checkpoint=checkpoint,
                                 start=start,
                                 end=end,
                                 follow=follow,
                                 execution_id=execution_id,
                                 function_name=function_name,
                                 replica_id=replica_id,
                                 system=system,
                                 text=text,
                                 view=view,
                                 until_completed=until_completed)

    def open_in_web(self):
        """
        Open the service in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def checkout(self):
        """
        Checkout

        :return:
        """
        return self.services.checkout(service=self)

    def pause(self):
        """
        pause

        :return:
        """
        return self.services.pause(service_id=self.id)

    def resume(self):
        """
        resume

        :return:
        """
        return self.services.resume(service_id=self.id)

    def execute(
            self,
            execution_input=None,
            function_name=None,
            resource=None,
            item_id=None,
            dataset_id=None,
            annotation_id=None,
            project_id=None,
            sync=False,
            stream_logs=True,
            return_output=True
    ):
        """
        Execute a function on an existing service

        :param List[FunctionIO] or dict execution_input: input dictionary or list of FunctionIO entities
        :param str function_name: function name to run
        :param str resource: input type.
        :param str item_id: optional - item id as input to function
        :param str dataset_id: optional - dataset id as input to function
        :param str annotation_id: optional - annotation id as input to function
        :param str project_id: resource's project
        :param bool sync: if true, wait for function to end
        :param bool stream_logs: prints logs of the new execution. only works with sync=True
        :param bool return_output: if True and sync is True - will return the output directly
        :return: execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.execute(function_name='function_name', item_id='item_id', project_id='project_id')
        """
        execution = self.executions.create(sync=sync,
                                           execution_input=execution_input,
                                           function_name=function_name,
                                           resource=resource,
                                           item_id=item_id,
                                           dataset_id=dataset_id,
                                           annotation_id=annotation_id,
                                           stream_logs=stream_logs,
                                           project_id=project_id,
                                           return_output=return_output)
        return execution

    def activate_slots(
            self,
            project_id: str = None,
            task_id: str = None,
            dataset_id: str = None,
            org_id: str = None,
            user_email: str = None,
            slots=None,
            role=None,
            prevent_override: bool = True,
            visible: bool = True,
            icon: str = 'fas fa-magic',
            **kwargs
    ) -> object:
        """
        Activate service slots

        :param str project_id: project id
        :param str task_id: task id
        :param str dataset_id: dataset id
        :param str org_id: org id
        :param str user_email: user email
        :param list slots: list of entities.PackageSlot
        :param str role: user role MemberOrgRole.ADMIN, MemberOrgRole.owner, MemberOrgRole.MEMBER
        :param bool prevent_override: True to prevent override
        :param bool visible: visible
        :param str icon: icon
        :param kwargs: all additional arguments
        :return: list of user setting for activated slots
        :rtype: list

        **Example**:

        .. code-block:: python

            service.activate_slots(project_id='project_id',
                                    slots=List[entities.PackageSlot],
                                    icon='fas fa-magic')
        """
        return self.services.activate_slots(
            service=self,
            project_id=project_id,
            task_id=task_id,
            dataset_id=dataset_id,
            org_id=org_id,
            user_email=user_email,
            slots=slots,
            role=role,
            prevent_override=prevent_override,
            visible=visible,
            icon=icon,
            **kwargs
        )


class InstanceCatalog(str, Enum):
    REGULAR_XS = "regular-xs"
    REGULAR_S = "regular-s"
    REGULAR_M = "regular-m"
    REGULAR_L = "regular-l"
    REGULAR_XL = "regular-xl"
    HIGHMEM_XS = "highmem-xs"
    HIGHMEM_S = "highmem-s"
    HIGHMEM_M = "highmem-m"
    HIGHMEM_L = "highmem-l"
    HIGHMEM_XL = "highmem-xl"
    GPU_K80_S = "gpu-k80-s"
    GPU_K80_M = "gpu-k80-m"


class KubernetesAutuscalerType(str, Enum):
    RABBITMQ = 'rabbitmq'
    CPU = 'cpu'


class KubernetesAutoscaler(entities.BaseEntity):
    MIN_REPLICA_DEFAULT = 0
    MAX_REPLICA_DEFAULT = 1
    AUTOSCALER_TYPE_DEFAULT = KubernetesAutuscalerType.RABBITMQ

    def __init__(self,
                 autoscaler_type: KubernetesAutuscalerType.RABBITMQ = AUTOSCALER_TYPE_DEFAULT,
                 min_replicas=MIN_REPLICA_DEFAULT,
                 max_replicas=MAX_REPLICA_DEFAULT,
                 cooldown_period=None,
                 polling_interval=None,
                 **kwargs):
        self.autoscaler_type = kwargs.get('type', autoscaler_type)
        self.min_replicas = kwargs.get('minReplicas', min_replicas)
        self.max_replicas = kwargs.get('maxReplicas', max_replicas)
        self.cooldown_period = kwargs.get('cooldownPeriod', cooldown_period)
        self.polling_interval = kwargs.get('pollingInterval', polling_interval)

    def to_json(self):
        _json = {
            'type': self.autoscaler_type,
            'minReplicas': self.min_replicas,
            'maxReplicas': self.max_replicas
        }

        if self.cooldown_period is not None:
            _json['cooldownPeriod'] = self.cooldown_period

        if self.polling_interval is not None:
            _json['pollingInterval'] = self.polling_interval

        return _json


class KubernetesRabbitmqAutoscaler(KubernetesAutoscaler):
    QUEUE_LENGTH_DEFAULT = 1000

    def __init__(self,
                 min_replicas=KubernetesAutoscaler.MIN_REPLICA_DEFAULT,
                 max_replicas=KubernetesAutoscaler.MAX_REPLICA_DEFAULT,
                 queue_length=QUEUE_LENGTH_DEFAULT,
                 cooldown_period=None,
                 polling_interval=None,
                 **kwargs):
        super().__init__(min_replicas=min_replicas,
                         max_replicas=max_replicas,
                         autoscaler_type=KubernetesAutuscalerType.RABBITMQ,
                         cooldown_period=cooldown_period,
                         polling_interval=polling_interval, **kwargs)
        self.queue_length = kwargs.get('queueLength', queue_length)

    def to_json(self):
        _json = super().to_json()
        _json['queueLength'] = self.queue_length
        return _json


class RuntimeType(str, Enum):
    KUBERNETES = 'kubernetes'


class ServiceRuntime(entities.BaseEntity):
    def __init__(self, service_type: RuntimeType = RuntimeType.KUBERNETES):
        self.service_type = service_type


class KubernetesRuntime(ServiceRuntime):
    DEFAULT_POD_TYPE = InstanceCatalog.REGULAR_S
    DEFAULT_NUM_REPLICAS = 1
    DEFAULT_CONCURRENCY = 10

    def __init__(self,
                 pod_type: InstanceCatalog = DEFAULT_POD_TYPE,
                 num_replicas=DEFAULT_NUM_REPLICAS,
                 concurrency=DEFAULT_CONCURRENCY,
                 runner_image=None,
                 autoscaler=None,
                 **kwargs):

        super().__init__(service_type=RuntimeType.KUBERNETES)
        self.pod_type = kwargs.get('podType', pod_type)
        self.num_replicas = kwargs.get('numReplicas', num_replicas)
        self.concurrency = kwargs.get('concurrency', concurrency)
        self.runner_image = kwargs.get('runnerImage', runner_image)
        self._proxy_image = kwargs.get('proxyImage', None)
        self.single_agent = kwargs.get('singleAgent', False)

        self.autoscaler = kwargs.get('autoscaler', autoscaler)
        if self.autoscaler is not None and isinstance(self.autoscaler, dict):
            if self.autoscaler['type'] == KubernetesAutuscalerType.RABBITMQ:
                self.autoscaler = KubernetesRabbitmqAutoscaler(**self.autoscaler)
            else:
                raise NotImplementedError(
                    'Unknown kubernetes autoscaler type: {}'.format(self.autoscaler['type']))

    def to_json(self):
        _json = {
            'podType': self.pod_type,
            'numReplicas': self.num_replicas,
            'concurrency': self.concurrency,
            'singleAgent': self.single_agent,
            'autoscaler': None if self.autoscaler is None else self.autoscaler.to_json()
        }

        if self.runner_image is not None:
            _json['runnerImage'] = self.runner_image

        if self._proxy_image is not None:
            _json['proxyImage'] = self._proxy_image

        return _json
