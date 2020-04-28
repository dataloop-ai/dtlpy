from collections import namedtuple
import traceback
import logging
import attr

from .. import services, repositories, entities, exceptions

logger = logging.getLogger("dataloop.service")


@attr.s
class Service(entities.BaseEntity):
    """
    Service object
    """
    # platform
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()
    version = attr.ib()

    package_id = attr.ib()
    package_revision = attr.ib()

    bot = attr.ib()
    use_user_jwt = attr.ib(repr=False)
    runtime = attr.ib(repr=False)  # hw requirements
    init_input = attr.ib()
    versions = attr.ib(repr=False)
    module_name = attr.ib()
    name = attr.ib()
    url = attr.ib()
    id = attr.ib()
    mq = attr.ib(repr=False)
    active = attr.ib()
    driver_id = attr.ib(repr=False)

    # name change
    project_id = attr.ib()
    is_global = attr.ib()

    # SDK
    _package = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    # repositories
    _project = attr.ib(default=None, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, package=None, project=None):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param package:
        :param project:
        :return:
        """
        try:
            service = Service.from_json(_json=_json,
                                        client_api=client_api,
                                        package=package,
                                        project=project)
            status = True
        except Exception:
            service = traceback.format_exc()
            status = False
        return status, service

    @classmethod
    def from_json(cls, _json, client_api, package=None, project=None, is_fetched=True):
        """

        :param _json:
        :param client_api:
        :param package:
        :param project:
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        versions = _json.get('versions', dict())
        inst = cls(
            package_revision=_json.get("packageRevision", None),
            bot=_json.get("botUserName", None),
            use_user_jwt=_json.get("useUserJwt", False),
            createdAt=_json.get("createdAt", None),
            updatedAt=_json.get("updatedAt", None),
            project_id=_json.get('projectId', None),
            package_id=_json.get('packageId', None),
            driver_id=_json.get('driverId', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            active=_json.get('active', None),
            runtime=_json.get("runtime", dict()),
            is_global=_json.get("global", False),
            init_input=_json.get("initParams", dict()),
            module_name=_json.get("moduleName", None),
            name=_json.get("name", None),
            url=_json.get("url", None),
            mq=_json.get('mq', dict()),
            id=_json.get("id", None),
            versions=versions,
            client_api=client_api,
            package=package,
            project=project
        )
        inst.is_fetched = is_fetched
        return inst

    ############
    # Entities #
    ############
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
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Service)._project,
                attr.fields(Service)._package,
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
                attr.fields(Service).driver_id)
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

        return _json

    def update(self):
        """
        Update Service changes to platform

        :return: Service entity
        """
        return self.services.update(service=self)

    def delete(self):
        """
        Delete Service object

        :return: True
        """
        return self.services.delete(service_id=self.id)

    def status(self):
        """
        Get Service status

        :return: True
        """
        return self.services.status(service_id=self.id)

    def log(self, size=None, checkpoint=None, start=None, end=None, follow=False,
            execution_id=None, function_name=None, replica_id=None, system=False, view=False):
        """
        Get service logs

        :param view:
        :param system:
        :param end: iso format time
        :param start: iso format time
        :param checkpoint:
        :param follow: filters
        :param execution_id: follow
        :param function_name: execution_id
        :param replica_id: function_name
        :param size:
        :return: Service entity
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
                                 view=view)

    def open_in_web(self):
        self.services.open_in_web(service=self)

    def checkout(self):
        """
        Checkout

        :return:
        """
        return self.services.checkout(service=self)

    def execute(self,
                # executions info
                execution_input=None, function_name=None,
                # inputs info
                resource=None, item_id=None, dataset_id=None, annotation_id=None, project_id=None,
                # execution config
                sync=False, stream_logs=True, return_output=True):
        """
        Execute a function on an existing service

        :param service_id: service id to execute on
        :param function_name: function name to run
        :param project_id: resource's project
        :param execution_input: input dictionary or list of FunctionIO entities
        :param dataset_id: optional - input to function
        :param item_id: optional - input to function
        :param annotation_id: optional - input to function
        :param resource: input type.
        :param sync: wait for function to end
        :param stream_logs: prints logs of the new execution. only works with sync=True
        :param return_output: if True and sync is True - will return the output directly
        :return:
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
