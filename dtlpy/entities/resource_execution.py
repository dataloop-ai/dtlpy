import attr
import logging
import traceback

from .. import repositories, entities, services

logger = logging.getLogger(name='dtlpy')


@attr.s
class ResourceExecution(entities.BaseEntity):
    """
    Resource execution entity
    """
    # platform
    resource_id = attr.ib()
    resource_type = attr.ib()
    execution_id = attr.ib()
    status = attr.ib()
    timestamp = attr.ib()
    progress = attr.ib()
    message = attr.ib()
    error = attr.ib()
    service_name = attr.ib()
    function_name = attr.ib()
    module_name = attr.ib()
    package_name = attr.ib()
    org_name = attr.ib()
    creator = attr.ib()
    project_id = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _project = attr.ib()
    resource = attr.ib()

    @staticmethod
    def _protected_from_json(_json, client_api, project=None, resource=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            execution = ResourceExecution.from_json(_json=_json,
                                                    client_api=client_api,
                                                    project=project,
                                                    resource=resource,
                                                    is_fetched=is_fetched)
            status = True
        except Exception:
            execution = traceback.format_exc()
            status = False
        return status, execution

    @classmethod
    def from_json(cls, _json, client_api, project=None, resource=None, is_fetched=True):
        """
        :param dict _json: platform json
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.project.Project project: project entity
        :param entity resource: an entity object (item, dataset, ...)
        :param is_fetched: is Entity fetched from Platform
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Execution has been fetched from a project that is not belong to it')
                project = None
        inst = cls(
            resource_id=_json.get('resourceId', None),
            resource_type=_json.get('resourceType', None),
            execution_id=_json.get('executionId', None),
            status=_json.get('status', None),
            timestamp=_json.get('timestamp', None),
            progress=_json.get('progress', None),
            message=_json.get('message', None),
            error=_json.get('error', None),
            service_name=_json.get('serviceName', None),
            function_name=_json.get('functionName', None),
            module_name=_json.get('moduleName', None),
            package_name=_json.get('packageName', None),
            org_name=_json.get('orgName', None),
            creator=_json.get('creator', None),
            project_id=_json.get('projectId', None),
            client_api=client_api,
            project=project,
            resource=resource,
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        # get excluded
        _json = attr.asdict(
            self, filter=attr.filters.exclude(
                attr.fields(ResourceExecution)._client_api,
                attr.fields(ResourceExecution)._project,
                attr.fields(ResourceExecution).resource_id,
                attr.fields(ResourceExecution).resource_type,
                attr.fields(ResourceExecution).execution_id,
                attr.fields(ResourceExecution).function_name,
                attr.fields(ResourceExecution).service_name,
                attr.fields(ResourceExecution).module_name,
                attr.fields(ResourceExecution).package_name,
                attr.fields(ResourceExecution).org_name,
                attr.fields(ResourceExecution).project_id,
            )
        )

        # rename
        _json['projectId'] = self.project_id
        _json['resourceId'] = self.resource_id
        _json['resourceType'] = self.resource_type
        _json['functionName'] = self.function_name
        _json['executionId'] = self.execution_id
        _json['serviceName'] = self.service_name
        _json['moduleName'] = self.module_name
        _json['packageName'] = self.package_name
        _json['orgName'] = self.org_name

        return _json

    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

