from collections import namedtuple
import logging
import traceback
from enum import Enum
from typing import List
import attr
from .node import PipelineNode, PipelineConnection, TaskNode, CodeNode, FunctionNode, DatasetNode
from .. import repositories, entities
from ..services.api_client import ApiClient
from .package_function import PackageInputType
import copy

logger = logging.getLogger(name='dtlpy')


class PipelineResumeOption(str, Enum):
    TERMINATE_EXISTING_CYCLES = 'terminateExistingCycles',
    RESUME_EXISTING_CYCLES = 'resumeExistingCycles'


class CompositionStatus(str, Enum):
    CREATED = "Created",
    INITIALIZING = "Initializing",
    INSTALLED = "Installed",
    ACTIVATED = "Activated",
    DEACTIVATED = "Deactivated",
    UNINSTALLED = "Uninstalled",
    TERMINATING = "Terminating",
    TERMINATED = "Terminated",
    UPDATING = "Updating",
    FAILURE = "Failure"


class PipelineSettings:

    def __init__(
            self,
            default_resume_option: PipelineResumeOption = None,
            keep_triggers_active: bool = None,
            active_trigger_ask_again: bool = None,
            last_update: dict = None
    ):
        self.default_resume_option = default_resume_option
        self.keep_triggers_active = keep_triggers_active
        self.active_trigger_ask_again = active_trigger_ask_again
        self.last_update = last_update

    @classmethod
    def from_json(cls, _json: dict = None):
        if _json is None:
            _json = dict()
        return cls(
            default_resume_option=_json.get('defaultResumeOption', None),
            keep_triggers_active=_json.get('keepTriggersActive', None),
            active_trigger_ask_again=_json.get('activeTriggerAskAgain', None),
            last_update=_json.get('lastUpdate', None)
        )

    def to_json(self):
        _json = dict()

        if self.default_resume_option is not None:
            _json['defaultResumeOption'] = self.default_resume_option

        if self.default_resume_option is not None:
            _json['keepTriggersActive'] = self.default_resume_option

        if self.default_resume_option is not None:
            _json['activeTriggerAskAgain'] = self.default_resume_option

        if self.default_resume_option is not None:
            _json['lastUpdate'] = self.default_resume_option

        return _json


class Variable(entities.DlEntity):
    """
    Pipeline Variables
    """
    id: str = entities.DlProperty(location=['id'], _type=str)
    created_at: str = entities.DlProperty(location=['createdAt'], _type=str)
    updated_at: str = entities.DlProperty(location=['updatedAt'], _type=str)
    reference: str = entities.DlProperty(location=['reference'], _type=str)
    creator: str = entities.DlProperty(location=['creator'], _type=str)
    variable_type: PackageInputType = entities.DlProperty(location=['type'], _type=PackageInputType)
    name: str = entities.DlProperty(location=['name'], _type=str)
    value = entities.DlProperty(location=['value'])

    @classmethod
    def from_json(cls, _json):
        """
        Turn platform representation of variable into a pipeline variable entity

        :param dict _json: platform representation of pipeline variable
        :return: pipeline variable entity
        :rtype: dtlpy.entities.pipeline.PipelineVariables
        """

        inst = cls(_dict=_json)
        return inst

    def to_json(self):
        """
        :return: variable of pipeline
        :rtype: dict
        """
        _json = self._dict.copy()
        return _json


class PipelineAverages:
    def __init__(
            self,
            avg_time_per_execution: float,
            avg_execution_per_day: float
    ):
        self.avg_time_per_execution = avg_time_per_execution
        self.avg_execution_per_day = avg_execution_per_day

    @classmethod
    def from_json(cls, _json: dict = None):
        if _json is None:
            _json = dict()
        return cls(
            avg_time_per_execution=_json.get('avgTimePerExecution', 'NA'),
            avg_execution_per_day=_json.get('avgExecutionsPerDay', 'NA')
        )


class NodeAverages:
    def __init__(
            self,
            node_id: str,
            averages: PipelineAverages
    ):
        self.node_id = node_id
        self.averages = averages

    @classmethod
    def from_json(cls, _json: dict):
        return cls(
            node_id=_json.get('nodeId', None),
            averages=PipelineAverages.from_json(_json.get('executionStatistics'))
        )


class PipelineCounter:
    def __init__(
            self,
            status: str,
            count: int
    ):
        self.status = status
        self.count = count


class NodeCounters:
    def __init__(
            self,
            node_id: str,
            counters: List[PipelineCounter]
    ):
        self.node_id = node_id
        self.counters = counters

    @classmethod
    def from_json(cls, _json: dict):
        return cls(
            node_id=_json.get('nodeId', None),
            counters=[PipelineCounter(**c) for c in _json.get('statusCount', list())],
        )


class PipelineStats:
    def __init__(
            self,
            pipeline_counters: List[PipelineCounter],
            node_counters: List[NodeCounters],
            pipeline_averages: PipelineAverages,
            node_averages: List[NodeAverages]
    ):
        self.pipeline_counters = pipeline_counters
        self.node_counters = node_counters
        self.pipeline_averages = pipeline_averages
        self.node_averages = node_averages

    @classmethod
    def from_json(cls, _json: dict):
        return cls(
            pipeline_counters=[PipelineCounter(**c) for c in _json.get('pipelineExecutionCounters', list())],
            node_counters=[NodeCounters.from_json(_json=c) for c in _json.get('nodeExecutionsCounters', list())],
            pipeline_averages=PipelineAverages.from_json(_json.get('pipelineExecutionStatistics', None)),
            node_averages=[NodeAverages.from_json(_json=c) for c in _json.get('nodeExecutionStatistics', list())]
        )


@attr.s
class Pipeline(entities.BaseEntity):
    """
    Pipeline object
    """
    # platform
    id = attr.ib()
    name = attr.ib()
    creator = attr.ib()
    org_id = attr.ib()
    connections = attr.ib()
    settings = attr.ib(type=PipelineSettings)
    variables = attr.ib(type=List[Variable])

    status = attr.ib(type=CompositionStatus)

    # name change
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    start_nodes = attr.ib()
    project_id = attr.ib()
    composition_id = attr.ib()
    url = attr.ib()
    preview = attr.ib()
    description = attr.ib()
    revisions = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _original_settings = attr.ib(repr=False, type=PipelineSettings)
    _original_variables = attr.ib(repr=False, type=List[Variable])
    _repositories = attr.ib(repr=False)

    updated_by = attr.ib(default=None)

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform json
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
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

        :param dict _json: platform representation of package
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.project.Project project: project entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: Pipeline entity
        :rtype: dtlpy.entities.pipeline.Pipeline
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Pipeline has been fetched from a project that is not belong to it')
                project = None

        connections = [PipelineConnection.from_json(_json=con) for con in _json.get('connections', list())]
        json_variables = _json.get('variables', None) or list()
        variables = list()
        if json_variables:
            copy_json_variables = copy.deepcopy(json_variables)
            variables = [Variable.from_json(_json=v) for v in copy_json_variables]

        settings = PipelineSettings.from_json(_json=_json.get('settings', dict()))
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
            connections=connections,
            start_nodes=_json.get('startNodes', None),
            url=_json.get('url', None),
            preview=_json.get('preview', None),
            description=_json.get('description', None),
            revisions=_json.get('revisions', None),
            settings=settings,
            variables=variables,
            status=_json.get('status', None),
            original_settings=settings,
            original_variables=json_variables,
            updated_by=_json.get('updatedBy', None),
        )
        for node in _json.get('nodes', list()):
            inst.nodes.add(node=cls.pipeline_node(node))
        inst.is_fetched = is_fetched
        return inst

    @classmethod
    def pipeline_node(self, _json):
        node_type = _json.get('type')
        if node_type == 'task':
            return TaskNode.from_json(_json)
        elif node_type == 'code':
            return CodeNode.from_json(_json)
        elif node_type == 'function':
            return FunctionNode.from_json(_json)
        elif node_type == 'storage':
            return DatasetNode.from_json(_json)
        else:
            return PipelineNode.from_json(_json)

    def settings_changed(self) -> bool:
        return self.settings.to_json() != self._original_settings.to_json()

    def variables_changed(self) -> bool:
        new_vars = [var.to_json() for var in self.variables]
        old_vars = self._original_variables or list()
        return new_vars != old_vars

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
        :rtype: dict
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Pipeline)._project,
                                                        attr.fields(Pipeline)._repositories,
                                                        attr.fields(Pipeline)._client_api,
                                                        attr.fields(Pipeline).project_id,
                                                        attr.fields(Pipeline).org_id,
                                                        attr.fields(Pipeline).connections,
                                                        attr.fields(Pipeline).created_at,
                                                        attr.fields(Pipeline).updated_at,
                                                        attr.fields(Pipeline).start_nodes,
                                                        attr.fields(Pipeline).project_id,
                                                        attr.fields(Pipeline).composition_id,
                                                        attr.fields(Pipeline).url,
                                                        attr.fields(Pipeline).preview,
                                                        attr.fields(Pipeline).description,
                                                        attr.fields(Pipeline).revisions,
                                                        attr.fields(Pipeline).settings,
                                                        attr.fields(Pipeline).variables,
                                                        attr.fields(Pipeline)._original_settings,
                                                        attr.fields(Pipeline)._original_variables,
                                                        attr.fields(Pipeline).updated_by,
                                                        ))

        _json['projectId'] = self.project_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['compositionId'] = self.composition_id
        _json['startNodes'] = self.start_nodes
        _json['orgId'] = self.org_id
        _json['nodes'] = [node.to_json() for node in self.nodes]
        _json['connections'] = [con.to_json() for con in self.connections]
        if self.variables:
            _json['variables'] = [v.to_json() for v in self.variables]
        _json['url'] = self.url

        settings_json = self.settings.to_json()
        if settings_json:
            _json['settings'] = settings_json

        if self.preview is not None:
            _json['preview'] = self.preview
        if self.description is not None:
            _json['description'] = self.description
        if self.revisions is not None:
            _json['revisions'] = self.revisions
        if self.updated_by is not None:
            _json['updatedBy'] = self.updated_by

        return _json

    #########
    # Props #
    #########

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/pipelines/{}".format(self.project_id, self.id))

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
                          field_names=['projects', 'pipelines', 'pipeline_executions', 'triggers', 'nodes'])

        r = reps(
            projects=repositories.Projects(client_api=self._client_api),
            pipelines=repositories.Pipelines(client_api=self._client_api, project=self._project),
            pipeline_executions=repositories.PipelineExecutions(
                client_api=self._client_api, project=self._project, pipeline=self
            ),
            triggers=repositories.Triggers(client_api=self._client_api, pipeline=self),
            nodes=repositories.Nodes(client_api=self._client_api, pipeline=self)
        )
        return r

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def nodes(self):
        assert isinstance(self._repositories.nodes, repositories.Nodes)
        return self._repositories.nodes

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
        """
        Open the pipeline in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def install(self, resume_option: PipelineResumeOption = None):
        """
        install pipeline

        :return: Composition entity
        """
        return self.pipelines.install(pipeline=self, resume_option=resume_option)

    def pause(self, keep_triggers_active: bool = None):
        """
        pause pipeline

        :return: Composition entity
        """
        return self.pipelines.pause(pipeline=self, keep_triggers_active=keep_triggers_active)

    def execute(self, execution_input=None):
        """
        execute a pipeline and return to execute

        :param execution_input: list of the dl.FunctionIO or dict of pipeline input - example {'item': 'item_id'}
        :return: entities.PipelineExecution object
        """
        execution = self.pipeline_executions.create(pipeline_id=self.id, execution_input=execution_input)
        return execution

    def execute_batch(self,
                      filters,
                      execution_inputs=None,
                      wait=True):
        """
        execute a pipeline and return to execute

        :param execution_inputs: list of the dl.FunctionIO or dict of pipeline input - example {'item': 'item_id'}, that represent the extra inputs of the function
        :param filters: Filters entity for a filtering before execute
        :param bool wait: wait until create task finish
        :return: entities.PipelineExecution object

        **Example**:

        .. code-block:: python

            command = pipeline.execute_batch(
                        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
                        filters=dl.Filters(field='dir', values='/test', context={'datasets': [dataset.id]))
        """
        command = self.pipeline_executions.create_batch(pipeline_id=self.id,
                                                        execution_inputs=execution_inputs,
                                                        filters=filters,
                                                        wait=wait)
        return command

    def reset(self, stop_if_running: bool = False):
        """
        Resets pipeline counters

        :param bool stop_if_running: If the pipeline is installed it will stop the pipeline and reset the counters.
        :return: bool
        """
        return self.pipelines.reset(pipeline_id=self.id, stop_if_running=stop_if_running)

    def stats(self):
        """
        Get pipeline counters

        :return: PipelineStats
        :rtype: dtlpy.entities.pipeline.PipelineStats
        """
        return self.pipelines.stats(pipeline_id=self.id)

    def set_start_node(self, node: PipelineNode):
        """
        Set the start node of the pipeline

        :param PipelineNode node: node to be the start node
        """
        connections = [connection for connection in self.connections if connection.target.node_id == node.node_id]
        if connections:
            raise Exception(
                'Connections cannot be added to Pipeline start-node. To add a connection, please reposition the start sign')
        if self.start_nodes:
            for pipe_node in self.start_nodes:
                if pipe_node['type'] == 'root':
                    pipe_node['nodeId'] = node.node_id
        else:
            self.start_nodes = [{"nodeId": node.node_id,
                                 "type": "root", }]

    def update_variables_values(self, **kwargs):
        """
        Update pipeline variables values for the given keyword arguments.

        **Example**:

        .. code-block:: python
            pipeline.update_variables_values(
                dataset=dataset.id,
                model=model.id,
                threshold=0.9
            )
            pipeline.update()
        """
        keys = kwargs.keys()
        for variable in self.variables:
            if variable.name in keys:
                variable.value = kwargs[variable.name]

