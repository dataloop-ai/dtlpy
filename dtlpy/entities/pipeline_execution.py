from collections import namedtuple
import logging
import traceback
from enum import Enum

import attr

from .. import repositories, entities
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class PipelineExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    FAILED = "failed"
    SUCCESS = "success"
    QUEUE = "queue"
    TERMINATED = "terminated"
    RERUN = "rerun"


class CycleRerunMethod(str, Enum):
    START_FROM_NODES = 'startFromNodes',
    START_FROM_FAILED_EXECUTIONS = 'startFromFailedExecutions',
    START_FROM_BEGINNING = 'startFromBeginning'


class PipelineExecutionNode:
    def __init__(self, name, node_id, ports, metadata, node_type, namespace, project_id, status):
        self.node_id = node_id
        self.namespace = namespace
        self.node_type = node_type
        self.status = status
        self.ports = ports
        self.metadata = metadata
        self.project_id = project_id
        self.name = name

    @staticmethod
    def from_json(_json: dict):
        ports = [entities.PipelineNodeIO.from_json(_json=i_input) for i_input in _json.get('ports', list())]
        return PipelineExecutionNode(
            node_id=_json.get('id', None),
            namespace=_json.get('namespace', None),
            node_type=_json.get('type', None),
            status=_json.get('status', None),
            ports=ports,
            metadata=_json.get('metadata', None),
            project_id=_json.get('projectId', None),
            name=_json.get('name', None),
        )

    def to_json(self):
        _json = {
            'id': self.node_id,
            'namespace': self.namespace,
            'type': self.node_type,
            'status': self.status,
            'ports': [_io.to_json() for _io in self.ports],
            'metadata': self.metadata,
            'projectId': self.project_id,
            'name': self.name,
        }

        return _json


@attr.s
class PipelineExecution(entities.BaseEntity):
    """
    Package object
    """
    # platform
    id = attr.ib()
    nodes = attr.ib(repr=False)
    executions = attr.ib(repr=False)
    status = attr.ib()
    # name change
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    pipeline_id = attr.ib()
    max_attempts = attr.ib()
    creator = attr.ib()

    # sdk
    _pipeline = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, pipeline=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform json
        :param client_api: ApiClient entity
        :param pipeline: Pipeline entity
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        try:
            pipeline = PipelineExecution.from_json(
                _json=_json,
                client_api=client_api,
                pipeline=pipeline,
                is_fetched=is_fetched
            )
            status = True
        except Exception:
            pipeline = traceback.format_exc()
            status = False
        return status, pipeline

    @classmethod
    def from_json(cls, _json, client_api, pipeline=None, is_fetched=True) -> 'PipelineExecution':
        """
        Turn platform representation of pipeline_execution into a pipeline_execution entity

        :param dict _json: platform representation of package
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.pipeline.Pipeline pipeline: Pipeline entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: Pipeline entity
        :rtype: dtlpy.entities.PipelineExecution
        """
        project = None
        if pipeline is not None:
            project = pipeline._project
            if pipeline.id != _json.get('pipelineId', None):
                logger.warning('Pipeline has been fetched from a project that is not belong to it')
                pipeline = None

        nodes = [PipelineExecutionNode.from_json(_json=node) for node in _json.get('nodes', list())]

        inst = cls(
            id=_json.get('id', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            pipeline_id=_json.get('pipelineId', None),
            status=_json.get('status', None),
            max_attempts=_json.get('maxAttempts', None),
            creator=_json.get('creator', None),
            nodes=nodes,
            executions=_json.get('executions', dict()),
            pipeline=pipeline,
            project=project,
            client_api=client_api,
        )

        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
        :rtype: dict
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(PipelineExecution)._repositories,
                                                        attr.fields(PipelineExecution)._client_api,
                                                        attr.fields(PipelineExecution)._pipeline,
                                                        attr.fields(PipelineExecution).nodes,
                                                        attr.fields(PipelineExecution).created_at,
                                                        attr.fields(PipelineExecution).updated_at,
                                                        attr.fields(PipelineExecution).pipeline_id,
                                                        attr.fields(PipelineExecution).executions,
                                                        attr.fields(PipelineExecution).max_attempts
                                                        ))
        executions = dict()
        for node_id, executions_list in self.executions.items():
            if len(executions_list) > 0 and isinstance(executions_list[0], entities.Execution):
                executions[node_id] = [e.to_json() for e in executions_list]
            else:
                executions[node_id] = executions_list

        _json['pipelineId'] = self.pipeline_id
        _json['maxAttempts'] = self.max_attempts
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['nodes'] = [node.to_json() for node in self.nodes]
        _json['executions'] = executions
        return _json

    #########
    # Props #
    #########
    @property
    def pipeline(self):
        if self._pipeline is None:
            self._pipeline = self.pipelines.get(pipeline_id=self.pipeline_id, fetch=None)
        assert isinstance(self._pipeline, entities.Pipeline)
        return self._pipeline

    @property
    def project(self):
        if self._project is None:
            self._project = self.pipeline.project
        assert isinstance(self._pipeline.project, entities.Project)
        return self._pipeline.project

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'pipelines', 'pipeline_executions'])

        r = reps(
            projects=repositories.Projects(client_api=self._client_api),
            pipelines=repositories.Pipelines(client_api=self._client_api, project=self._project),
            pipeline_executions=repositories.PipelineExecutions(client_api=self._client_api,
                                                                project=self._project,
                                                                pipeline=self._pipeline)
        )
        return r

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def pipelines(self):
        assert isinstance(self._repositories.pipelines, repositories.Pipelines)
        return self._repositories.pipelines

    @property
    def pipeline_executions(self):
        assert isinstance(self._repositories.pipeline_executions, repositories.PipelineExecutions)
        return self._repositories.pipeline_executions

    def rerun(self,
              method: str = None,
              start_nodes_ids: list = None,
              wait: bool = True
              ) -> bool:
        """
        Get Pipeline Execution object

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str method: method to run
        :param list start_nodes_ids: list of start nodes ids
        :param bool wait: wait until rerun finish
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            pipeline_executions.rerun(method=dl.CycleRerunMethod.START_FROM_BEGINNING,)
        """
        filters = entities.Filters(field='id', values=[self.id], operator=entities.FiltersOperations.IN,
                                   resource=entities.FiltersResource.PIPELINE_EXECUTION)
        return self.pipeline_executions.rerun(
            method=method,
            start_nodes_ids=start_nodes_ids,
            filters=filters,
            wait=wait
        )

    def wait(self):
        """
        Wait for pipeline execution

        :return: Pipeline execution object
        """
        return self.pipeline_executions.wait(pipeline_execution_id=self.id)

    def in_progress(self):
        return self.status not in [PipelineExecutionStatus.FAILED,
                                   PipelineExecutionStatus.SUCCESS,
                                   PipelineExecutionStatus.TERMINATED]
