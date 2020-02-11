import attr
from .. import repositories, entities, services, exceptions


@attr.s
class Execution:
    """
    Service execution entity
    """
    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    creator = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    input = attr.ib()
    output = attr.ib()
    feedbackQueue = attr.ib(repr=False)
    status = attr.ib()
    syncReplyTo = attr.ib(repr=False)
    latest_status = attr.ib()
    function_name = attr.ib()

    # name changed
    trigger_id = attr.ib()
    service_id = attr.ib()
    pipeline_id = attr.ib()
    project_id = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _service = attr.ib(repr=False)
    _project = attr.ib(repr=False, default=None)

    @classmethod
    def from_json(cls, _json, client_api, service=None):
        return cls(
            feedbackQueue=_json.get('feedbackQueue', None),
            service_id=_json.get('serviceId', None),
            project_id=_json.get('projectId', None),
            pipeline_id=_json.get('pipelineId', None),
            latest_status=_json.get('latestStatus', None),
            syncReplyTo=_json.get('syncReplyTo', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            creator=_json.get('creator', None),
            trigger_id=_json.get('triggerId', None),
            output=_json.get('output', None),
            status=_json.get('status', None),
            function_name=_json.get('functionName', entities.DEFAULT_PACKAGE_FUNCTION_NAME),
            input=_json.get('input', None),
            url=_json.get('url', None),
            id=_json.get('id', None),
            client_api=client_api,
            service=service
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Execution)._client_api,
                                                              attr.fields(Execution)._service,
                                                              attr.fields(Execution).project_id,
                                                              attr.fields(Execution).service_id,
                                                              attr.fields(Execution).pipeline_id,
                                                              attr.fields(Execution).trigger_id,
                                                              attr.fields(Execution).function_name,
                                                              attr.fields(Execution).latest_status,
                                                              ))
        # rename
        _json['projectId'] = self.project_id
        _json['triggerId'] = self.trigger_id
        _json['serviceId'] = self.service_id
        _json['pipelineId'] = self.pipeline_id
        _json['functionName'] = self.function_name
        _json['latestStatus'] = self.latest_status
        return _json

    @property
    def service(self):
        if self._service is None:
            self.get_service()
            if self._service is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "service".')
        assert isinstance(self._service, entities.Service)
        return self._service

    @property
    def project(self):
        if self._project is None:
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    def get_latest_status(self):
        self.latest_status = repositories.Executions(client_api=self._client_api, service=self._service,
                                                     project=self._project).get(execution_id=self.id).latest_status
        return self.latest_status

    @service.setter
    def service(self, service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid service entity')
        self._service = service

    def get_service(self, dummy=False):
        if dummy:
            self._service = entities.Service.dummy(service_id=self.service_id, client_api=self._client_api)
        else:
            self._service = self.project.services.get(service_id=self.service_id)

    def get_project(self, dummy=False):
        if dummy:
            self._project = entities.Project.dummy(project_id=self.project_id, client_api=self._client_api)
        else:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id)

    def progress_update(self, status=None, percent_complete=None, message=None, output=None):
        """
        Update Execution Progress

        :param status:
        :param percent_complete:
        :param message:
        :param output:
        :return:
        """
        return self.service.executions.progress_update(execution_id=self.id,
                                                       status=status,
                                                       percent_complete=percent_complete,
                                                       message=message,
                                                       output=output)
