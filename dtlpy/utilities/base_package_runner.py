import datetime
import threading

from .. import entities


class BaseServiceRunner:
    _do_reset = False
    _auto_refresh_dtlpy_token = None
    _refresh_dtlpy_token = None
    _threads_terminated = list()
    _threads_terminated_lock = threading.Lock()
    _service_entity = None

    def do_reset(self):
        self._do_reset = True

    def _terminate(self, tid):
        with self._threads_terminated_lock:
            self._threads_terminated.append(tid)

    def kill_event(self):
        ident = threading.get_ident()
        if ident in self._threads_terminated:
            with self._threads_terminated_lock:
                self._threads_terminated.pop(self._threads_terminated.index(ident))
            raise InterruptedError('Execution received termination signal')

    @property
    def service_entity(self) -> entities.Service:
        assert isinstance(self._service_entity, entities.Service), "service_entity must be a dl.Service object"
        return self._service_entity

    @service_entity.setter
    def service_entity(self, value):
        assert isinstance(value, entities.Service), "service_entity must be a dl.Service object"
        self._service_entity = value


class Progress:
    def update(self, status=None, progress=0, message=None, output=None):
        pass


class ItemStatusEvent:
    def __init__(self, _json: dict):
        if _json is None:
            _json = dict()

        self.pipeline_id = _json.get('pipelineId', None)
        self.node_id = _json.get('nodeId', None)
        self.action = _json.get('action', None)
        self.task_id = _json.get('status', dict()).get('taskId', None)
        self.assignment_id = _json.get('status', dict()).get('assignmentId', None)
        self.status = _json.get('status', dict()).get('status', None)
        self.creator = _json.get('status', dict()).get('creator', None)
        self.timestamp = _json.get('status', dict()).get('timestamp', None)


class ExecutionEventContext:
    def __init__(self, _json: dict):
        if _json is None:
            _json = dict()

        self.resource = _json.get('resource', None)
        self.source = _json.get('source', None)
        self.action = _json.get('action', None)
        self.resource_id = _json.get('resourceId', None)
        self.user_id = _json.get('userId', None)
        self.dataset_id = _json.get('datasetId', None)
        self.project_id = _json.get('projectId', None)
        self.body = _json.get('body', None)
        self.item_status_event = ItemStatusEvent(_json.get('itemStatusEvent', dict()))


class Context:

    def __init__(
            self,
            execution_dict: dict,
            service: entities.Service,
            package: entities.Package,
            project: entities.Project,
            event_context: dict,
            progress: Progress,
            logger,
            sdk
    ):

        # dtlpy
        self.logger = logger
        self.sdk = sdk
        self.progress = progress

        # objects
        self.service = service
        self.package = package
        self.project = project
        self.event = ExecutionEventContext(event_context)
        self.execution_dict = execution_dict

        # ids
        self.trigger_id = execution_dict.get('trigger_id', None)
        self.pipeline_id = execution_dict.get('pipeline', dict()).get('id')
        self.node_id = execution_dict.get('pipeline', dict()).get('nodeId')
        self.pipeline_execution_id = execution_dict.get('pipeline', dict()).get('executionId', None)
        self.execution_id = execution_dict['id']

        # props
        self._task = None
        self._assignment = None
        self._pipeline = None
        self._node = None
        self._execution = None
        self._pipeline_execution = None

    @property
    def item_status_creator(self):
        return self.event.item_status_event.creator

    @property
    def item_status(self):
        return self.event.item_status_event.status

    @property
    def item_status_operation(self):
        return self.event.item_status_event.action

    @property
    def execution(self) -> entities.Execution:
        if self._execution is None:
            # noinspection PyProtectedMember
            self._execution = self.sdk.Execution.from_json(
                _json=self.execution_dict,
                client_api=self.service._client_api,
                service=self.service,
                project=self.project
            )
        return self._execution

    @property
    def task_id(self) -> str:
        return self.event.item_status_event.task_id

    @property
    def task(self) -> entities.Task:
        if self._task is None and self.task_id is not None:
            try:
                self._task = self.sdk.tasks.get(task_id=self.task_id)
            except Exception:
                self.logger.exception('Failed to get task')
        return self._task

    @property
    def assignment_id(self) -> str:
        return self.event.item_status_event.assignment_id

    @property
    def assignment(self) -> entities.Assignment:
        if self._assignment is None and self.assignment_id is not None:
            self._assignment = self.sdk.assignments.get(assignment_id=self.assignment_id)
        return self._assignment

    @property
    def pipeline(self) -> entities.Pipeline:
        if self._pipeline is None and self.pipeline_id is not None:
            self._pipeline = self.sdk.pipelines.get(pipeline_id=self.pipeline_id)
        return self._pipeline

    @property
    def node(self):
        if self._node is None and self.pipeline is not None and self.node_id is not None:
            self._node = [n for n in self.pipeline.nodes if n.node_id == self.node_id][0]
        return self._node

    @property
    def pipeline_execution(self):
        if self._pipeline_execution is None and self.pipeline_execution_id is not None:
            self._pipeline_execution = self.sdk.pipeline_executions.get(
                pipeline_execution_id=self.pipeline_execution_id,
                pipeline_id=self.pipeline_id
            )
        return self._pipeline_execution
