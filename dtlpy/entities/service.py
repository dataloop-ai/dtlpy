from collections import namedtuple
import traceback
import logging
import attr

from .. import services, repositories, entities, miscellaneous, exceptions

logger = logging.getLogger("dataloop.service")


@attr.s
class Service:
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
    def from_json(cls, _json, client_api, package=None, project=None):
        versions = _json.get('versions', dict())
        return cls(
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

    @classmethod
    def dummy(cls, service_id, client_api):
        """
        Get a dummy entity
        :param service_id:
        :param client_api:
        :return:
        """
        return cls(
            package_revision=None,
            bot=None,
            use_user_jwt=None,
            createdAt=None,
            updatedAt=None,
            project_id=None,
            package_id=None,
            module_name=None,
            runtime=None,
            init_input=None,
            is_global=False,
            name=None,
            url=None,
            mq=None,
            id=service_id,
            versions=None,
            client_api=client_api,
            package=None,
            project=None,
            active=None,
            driver_id=None,
            version=None,
            creator=None
        )

    ############
    # Entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def package(self):
        if self._package is None:
            self.get_package()
            if self._package is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "package".')
        assert isinstance(self._package, entities.Package)
        return self._package

    def get_project(self, dummy=False):
        if self._project is None:
            if dummy:
                self._project = entities.Project.dummy(project_id=self.project_id, client_api=self._client_api)
            else:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id)

    def get_package(self, dummy=False):
        if self._package is None:
            if dummy:
                self._package = entities.Package.dummy(package_id=self.package_id, client_api=self._client_api)
            else:
                self._package = repositories.Packages(client_api=self._client_api).get(package_id=self.package_id)

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
    def print(self):
        miscellaneous.List([self]).print()

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

    def log(self, size=None, checkpoint=None, start=None, end=None):
        """
        Get service logs

        :param end:
        :param start:
        :param checkpoint:
        :param size:
        :return: Service entity
        """
        return self.services.log(service=self, size=size, checkpoint=checkpoint, start=start, end=end)

    def open_in_web(self):
        self.services.open_in_web(service=self)

    def checkout(self):
        """
        Checkout

        :return:
        """
        return self.services.checkout(service=self)

    def execute(self, sync=False, execution_input=None, function_name=None, resource=None, item_id=None,
                dataset_id=None, annotation_id=None):
        execution = repositories.Services(package=self._package,
                                          project=self._project,
                                          client_api=self._client_api).execute(service=self,
                                                                               sync=sync,
                                                                               execution_input=execution_input,
                                                                               function_name=function_name,
                                                                               resource=resource,
                                                                               item_id=item_id,
                                                                               dataset_id=dataset_id,
                                                                               annotation_id=annotation_id
                                                                               )
        return execution
