from collections import namedtuple
import logging
import traceback
import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


class PipelineNodeIO:
    def __init__(self, port_id, input_type, name, color, display_name):
        self.port_id = port_id
        self.input_type = input_type
        self.name = name
        self.color = color
        self.display_name = display_name

    @staticmethod
    def from_json(_json: dict):
        return PipelineNodeIO(
            port_id=_json.get('portId', None),
            input_type=_json.get('type', None),
            name=_json.get('name', None),
            color=_json.get('color', None),
            display_name=_json.get('displayName', None)
        )

    def to_json(self):
        _json = {
            'portId': self.port_id,
            'type': self.input_type,
            'name': self.name,
            'color': self.color,
            'displayName': self.display_name
        }
        return _json


class PipelineNode:
    def __init__(self, name, node_id, outputs, inputs, metadata, node_type, namespace, project_id):
        self.name = name
        self.node_id = node_id
        self.outputs = outputs
        self.inputs = inputs
        self.metadata = metadata
        self.node_type = node_type
        self.namespace = namespace
        self.project_id = project_id

    @staticmethod
    def from_json(_json: dict):
        inputs = [PipelineNodeIO.from_json(_json=i_input) for i_input in _json.get('inputs', list())]
        outputs = [PipelineNodeIO.from_json(_json=i_output) for i_output in _json.get('outputs', list())]
        return PipelineNode(
            name=_json.get('name', None),
            node_id=_json.get('nodeId', None),
            outputs=outputs,
            inputs=inputs,
            metadata=_json.get('metadata', None),
            node_type=_json.get('type', None),
            namespace=_json.get('namespace', None),
            project_id=_json.get('projectId', None)
        )

    def to_json(self):
        _json = {
            'name': self.name,
            'nodeId': self.node_id,
            'outputs': [_io.to_json() for _io in self.outputs],
            'inputs': [_io.to_json() for _io in self.inputs],
            'metadata': self.metadata,
            'type': self.node_type,
            'namespace': self.namespace,
            'projectId': self.project_id,
        }
        return _json


class PipelineConnectionPort:
    def __init__(self, node_id: str, port_id: str):
        self.node_id = node_id
        self.port_id = port_id

    @staticmethod
    def from_json(_json: dict):
        return PipelineConnectionPort(
            node_id=_json.get('nodeId', None),
            port_id=_json.get('portId', None),
        )

    def to_json(self):
        _json = {
            'nodeId': self.node_id,
            'portId': self.port_id,
        }
        return _json


class PipelineConnection:
    def __init__(self, source: PipelineConnectionPort, target: PipelineConnectionPort, condition):
        self.source = source
        self.target = target
        self.condition = condition

    @staticmethod
    def from_json(_json: dict):
        return PipelineConnection(
            source=PipelineConnectionPort.from_json(_json=_json.get('src', None)),
            target=PipelineConnectionPort.from_json(_json=_json.get('tgt', None)),
            condition=_json.get('condition', None),
        )

    def to_json(self):
        _json = {
            'src': self.source.to_json(),
            'tgt': self.target.to_json(),
            'condition': self.condition,
        }
        return _json


@attr.s
class Pipeline(entities.BaseEntity):
    """
    Package object
    """
    # platform
    id = attr.ib()
    name = attr.ib()
    creator = attr.ib()
    org_id = attr.ib()
    nodes = attr.ib()
    connections = attr.ib()

    # name change
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    start_nodes = attr.ib()
    project_id = attr.ib()
    composition_id = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :return:
        """
        try:
            pipeline = Pipeline.from_json(
                _json=_json,
                client_api=client_api,
                project=project,
                is_fetched=is_fetched
            )
            status = True
        except Exception:
            pipeline = traceback.format_exc()
            status = False
        return status, pipeline

    @classmethod
    def from_json(cls, _json, client_api, project, is_fetched=True):
        """
        Turn platform representation of pipeline into a pipeline entity

        :param _json: platform representation of package
        :param client_api:
        :param project:
        :param is_fetched: is Entity fetched from Platform
        :return: Package entity
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Pipeline has been fetched from a project that is not belong to it')
                project = None

        nodes = [PipelineNode.from_json(_json=node) for node in _json.get('nodes', list())]
        connections = [PipelineConnection.from_json(_json=con) for con in _json.get('connections', list())]
        inst = cls(
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            project_id=_json.get('projectId', None),
            org_id=_json.get('orgId', None),
            composition_id=_json.get('compositionId', None),
            creator=_json.get('creator', None),
            client_api=client_api,
            name=_json.get('name', None),
            project=project,
            id=_json.get('id', None),
            nodes=nodes,
            connections=connections,
            start_nodes=_json.get('startNodes', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Pipeline)._project,
                                                        attr.fields(Pipeline)._repositories,
                                                        attr.fields(Pipeline)._client_api,
                                                        attr.fields(Pipeline).project_id,
                                                        attr.fields(Pipeline).org_id,
                                                        attr.fields(Pipeline).nodes,
                                                        attr.fields(Pipeline).connections,
                                                        attr.fields(Pipeline).created_at,
                                                        attr.fields(Pipeline).updated_at,
                                                        attr.fields(Pipeline).start_nodes,
                                                        attr.fields(Pipeline).project_id,
                                                        attr.fields(Pipeline).composition_id,
                                                        ))

        _json['projectId'] = self.project_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['compositionId'] = self.project_id
        _json['startNodes'] = self.start_nodes
        _json['orgId'] = self.project_id
        _json['nodes'] = [node.to_json() for node in self.nodes]
        _json['connections'] = [con.to_json() for con in self.connections]

        return _json

    #########
    # Props #
    #########

    @property
    def project(self):
        if self._project is None:
            self._project = self.projects.get(project_id=self.project_id, fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'pipelines', 'pipeline_executions'])

        r = reps(
            projects=repositories.Projects(client_api=self._client_api),
            pipelines=repositories.Pipelines(client_api=self._client_api),
            pipeline_executions=repositories.PipelineExecutions(
                client_api=self._client_api, project=self._project, pipeline=self
            )
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

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update pipeline changes to platform

        :return: pipeline entity
        """
        return self.pipelines.update(pipeline=self)

    def delete(self):
        """
        Delete pipeline object

        :return: True
        """
        return self.pipelines.delete(pipeline=self)

    def open_in_web(self):
        self.pipelines.open_in_web(pipeline=self)
