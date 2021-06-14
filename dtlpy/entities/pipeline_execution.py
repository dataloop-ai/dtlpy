from collections import namedtuple
import logging
import traceback
import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


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
    nodes = attr.ib()
    executions = attr.ib()

    # name change
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    pipeline_id = attr.ib()
    pipeline_execution_id = attr.ib()

    # sdk
    _pipeline = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, pipeline, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
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
    def from_json(cls, _json, client_api, pipeline, is_fetched=True):
        """
        Turn platform representation of pipeline_execution into a pipeline_execution entity

        :param _json: platform representation of package
        :param client_api:
        :param pipeline:
        :param is_fetched: is Entity fetched from Platform
        :return: Package entity
        """
        if pipeline is not None:
            if pipeline.id != _json.get('pipelineId', None):
                logger.warning('Pipeline has been fetched from a project that is not belong to it')
                pipeline = None

        nodes = [PipelineExecutionNode.from_json(_json=node) for node in _json.get('nodes', list())]

        executions = _json.get('executions', dict())
        if len(executions) > 0:
            for node_id, executions_list in executions.items():
                if len(executions_list) > 0 and isinstance(executions_list[0], dict):
                    executions[node_id] = [
                        entities.Execution.from_json(
                            _json=execution,
                            client_api=client_api
                        ) for execution in executions_list
                    ]

        inst = cls(
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            pipeline_id=_json.get('pipelineId', None),
            pipeline_execution_id=_json.get('pipelineExecutionId', None),
            client_api=client_api,
            id=_json.get('id', None),
            nodes=nodes,
            executions=executions,
            pipeline=pipeline
        )

        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
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
                                                        attr.fields(PipelineExecution).pipeline_execution_id,
                                                        ))

        _json['pipelineId'] = self.pipeline_id
        _json['pipelineExecutionId'] = self.pipeline_execution_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['nodes'] = [node.to_json() for node in self.nodes]

        executions = dict()
        for node_id, executions_list in self.executions.items():
            if len(executions_list) > 0 and isinstance(executions_list[0], entities.Execution):
                executions[node_id] = [e.to_json() for e in executions_list]
            else:
                executions[node_id] = executions_list

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
        return self.pipeline.project

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'pipelines'])

        r = reps(
            projects=repositories.Projects(client_api=self._client_api),
            pipelines=repositories.Pipelines(client_api=self._client_api),
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
