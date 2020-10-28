import attr
import logging
import traceback
from collections import namedtuple

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


class ExecutionStatus:
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "inProgress"
    CREATED = "created"


@attr.s
class Execution(entities.BaseEntity):
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
    output = attr.ib(repr=False)
    feedbackQueue = attr.ib(repr=False)
    status = attr.ib(repr=False)
    syncReplyTo = attr.ib(repr=False)
    latest_status = attr.ib()
    function_name = attr.ib()
    duration = attr.ib()
    attempts = attr.ib()
    max_attempts = attr.ib()
    to_terminate = attr.ib(type=bool)

    # name changed
    trigger_id = attr.ib()
    service_id = attr.ib()
    pipeline_id = attr.ib()
    project_id = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _service = attr.ib(repr=False)
    _project = attr.ib(repr=False, default=None)
    _repositories = attr.ib(repr=False)

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['executions', 'services'])

        if self._project is not None:
            services_repo = self._project.services
            executions_repo = self._project.executions
        elif self._service is not None:
            services_repo = self._service.services
            executions_repo = self._service.executions
        else:
            services_repo = repositories.Services(client_api=self._client_api,
                                                  project=self._project,
                                                  package=None)
            executions_repo = repositories.Executions(client_api=self._client_api,
                                                      project=self._project,
                                                      service=self._service)

        r = reps(executions=executions_repo,
                 services=services_repo)
        return r

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @staticmethod
    def _protected_from_json(_json, client_api, project=None, service=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :return:
        """
        try:
            execution = Execution.from_json(_json=_json,
                                            client_api=client_api,
                                            project=None,
                                            service=service,
                                            is_fetched=is_fetched)
            status = True
        except Exception:
            execution = traceback.format_exc()
            status = False
        return status, execution

    @classmethod
    def from_json(cls, _json, client_api, project=None, service=None, is_fetched=True):
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Execution has been fetched from a project that is not belong to it')
                project = None

        if service is not None:
            if service.id != _json.get('serviceId', None):
                logger.warning('Execution has been fetched from a service that is not belong to it')
                service = None


        inst = cls(
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
            attempts=_json.get('attempts', None),
            max_attempts=_json.get('maxAttempts', None),
            output=_json.get('output', None),
            status=_json.get('status', None),
            duration=_json.get('duration', None),
            function_name=_json.get('functionName', entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME),
            input=_json.get('input', None),
            url=_json.get('url', None),
            id=_json.get('id', None),
            to_terminate=_json.get('toTerminate', False),
            client_api=client_api,
            project=project,
            service=service
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Execution)._client_api,
                                                              attr.fields(Execution)._service,
                                                              attr.fields(Execution)._project,
                                                              attr.fields(Execution).to_terminate,
                                                              attr.fields(Execution)._repositories,
                                                              attr.fields(Execution).project_id,
                                                              attr.fields(Execution).service_id,
                                                              attr.fields(Execution).pipeline_id,
                                                              attr.fields(Execution).trigger_id,
                                                              attr.fields(Execution).function_name,
                                                              attr.fields(Execution).max_attempts,
                                                              attr.fields(Execution).latest_status))
        # rename
        _json['projectId'] = self.project_id
        _json['triggerId'] = self.trigger_id
        _json['serviceId'] = self.service_id
        _json['pipelineId'] = self.pipeline_id
        _json['functionName'] = self.function_name
        _json['latestStatus'] = self.latest_status
        _json['maxAttempts'] = self.max_attempts
        _json['toTerminate'] = self.to_terminate
        return _json

    @property
    def service(self):
        if self._service is None:
            self._service = self.services.get(service_id=self.service_id, fetch=None)
        assert isinstance(self._service, entities.Service)
        return self._service

    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    def get_latest_status(self):
        self.latest_status = self.executions.get(execution_id=self.id).latest_status
        return self.latest_status

    @service.setter
    def service(self, service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid service entity')
        self._service = service

    def progress_update(self, status=None, percent_complete=None, message=None, output=None):
        """
        Update Execution Progress

        :param status:
        :param percent_complete:
        :param message:
        :param output:
        :return:
        """
        return self.executions.progress_update(execution_id=self.id,
                                               status=status,
                                               percent_complete=percent_complete,
                                               message=message,
                                               output=output)

    def update(self):
        """
        Update execution changes to platform
        :return: execution entity
        """
        return self.executions.update(execution=self)

    def logs(self, follow=False):
        """
        Print logs for execution
        """
        self.services.log(execution_id=self.id,
                          view=True,
                          service=self.service,
                          follow=follow)

    def increment(self):
        """
        Increment attempts

        :return:
        """
        self.attempts = self.executions.increment(execution=self)

    def terminate(self):
        """
        Terminate execution

        :return:
        """
        return self.executions.terminate(execution=self)

    def wait(self):
        """
        Wait for execution

        :return:
        """
        return self.executions.wait(execution_id=self.id)
