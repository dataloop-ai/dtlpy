import warnings

import inspect
import json
import logging
import uuid
from typing import Callable
from enum import Enum
from typing import List
import datetime

from .. import entities, assets, repositories, PlatformException

NODE_SIZE = (200, 87)

logger = logging.getLogger(name='dtlpy')


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
    def __init__(self,
                 source: PipelineConnectionPort,
                 target: PipelineConnectionPort,
                 filters: entities.Filters,
                 action: str = None
                 ):
        """
        :param PipelineConnectionPort source: the source pipeline connection
        :param PipelineConnectionPort target: the target pipeline connection
        :param entities.Filters filters: condition for the connection between the nodes
        :param str action: the action that move the input when it happen
        """
        self.source = source
        self.target = target
        self.filters = filters
        self.action = action

    @staticmethod
    def from_json(_json: dict):
        condition = _json.get('condition', None)
        if condition:
            condition = json.loads(condition)
        return PipelineConnection(
            source=PipelineConnectionPort.from_json(_json=_json.get('src', None)),
            target=PipelineConnectionPort.from_json(_json=_json.get('tgt', None)),
            filters=condition,
            action=_json.get('action', None)
        )

    def to_json(self):
        _json = {
            'src': self.source.to_json(),
            'tgt': self.target.to_json(),
        }
        if self.action:
            _json['action'] = self.action
        if self.filters:
            if isinstance(self.filters, entities.Filters):
                filters = self.filters.prepare(query_only=True).get('filter', dict())
            else:
                filters = self.filters

            _json['condition'] = json.dumps(filters)
        return _json


class PipelineNodeIO:
    def __init__(self,
                 input_type: entities.PackageInputType,
                 name: str,
                 display_name: str,
                 port_id: str = None,
                 color: tuple = None,
                 port_percentage: int = None,
                 action: str = None,
                 default_value=None,
                 variable_name: str = None,
                 actions: list = None):
        """
        Pipeline Node

        :param entities.PackageInputType input_type: entities.PackageInputType of the input type of the pipeline
        :param str name: name of the input
        :param str display_name: of the input
        :param str port_id: port id
        :param tuple color: tuple the display the color
        :param int port_percentage: port percentage
        :param str action: the action that move the input when it happen
        :param default_value: default value of the input
        :param list actions: the actions list that move the input when it happen
        """
        self.port_id = port_id if port_id else str(uuid.uuid4())
        self.input_type = input_type
        self.name = name
        self.color = color
        self.display_name = display_name
        self.port_percentage = port_percentage
        self.default_value = default_value
        self.variable_name = variable_name

        if action is not None:
            warnings.warn('action param has been deprecated in version 1.80', DeprecationWarning)
            if actions is None:
                actions = []
            actions.append(action)
        self.actions = actions

    @property
    def action(self):
        warnings.warn('action attribute has been deprecated in version 1.80', DeprecationWarning)
        return None

    @staticmethod
    def from_json(_json: dict):
        return PipelineNodeIO(
            port_id=_json.get('portId', None),
            input_type=_json.get('type', None),
            name=_json.get('name', None),
            color=_json.get('color', None),
            display_name=_json.get('displayName', None),
            port_percentage=_json.get('portPercentage', None),
            default_value=_json.get('defaultValue', None),
            variable_name=_json.get('variableName', None),
            actions=_json.get('actions', None),
        )

    def to_json(self):
        _json = {
            'portId': self.port_id,
            'type': self.input_type,
            'name': self.name,
            'color': self.color,
            'displayName': self.display_name,
            'variableName': self.variable_name,
            'portPercentage': self.port_percentage,
        }

        if self.actions:
            _json['actions'] = self.actions
        if self.default_value:
            _json['defaultValue'] = self.default_value

        return _json


class PipelineNodeType(str, Enum):
    TASK = 'task'
    CODE = 'code'
    FUNCTION = 'function'
    STORAGE = 'storage'
    ML = 'ml'


class PipelineNameSpace:
    def __init__(self, function_name, project_name, module_name=None, service_name=None, package_name=None):
        self.function_name = function_name
        self.project_name = project_name
        self.module_name = module_name
        self.service_name = service_name
        self.package_name = package_name

    def to_json(self):
        _json = {
            "functionName": self.function_name,
            "projectName": self.project_name
        }
        if self.module_name:
            _json['moduleName'] = self.module_name

        if self.service_name:
            _json['serviceName'] = self.service_name

        if self.package_name:
            _json['packageName'] = self.package_name
        return _json

    @staticmethod
    def from_json(_json: dict):
        return PipelineNameSpace(
            function_name=_json.get('functionName'),
            project_name=_json.get('projectName'),
            module_name=_json.get('moduleName', None),
            service_name=_json.get('serviceName', None),
            package_name=_json.get('packageName', None)
        )


class PipelineNode:
    def __init__(self,
                 name: str,
                 node_id: str,
                 outputs: list,
                 inputs: list,
                 node_type: PipelineNodeType,
                 namespace: PipelineNameSpace,
                 project_id: str,
                 metadata: dict = None,
                 config: dict = None,
                 position: tuple = (1, 1),
                 app_id: str = None,
                 ):
        """
        :param str name: node name
        :param str node_id: node id
        :param list outputs: list of PipelineNodeIO outputs
        :param list inputs: list of PipelineNodeIO inputs
        :param dict metadata: dict of the metadata of the node
        :param PipelineNodeType node_type: task, code, function
        :param PipelineNameSpace namespace: PipelineNameSpace of the node space
        :param str project_id: project id
        :param dict config: for the code node dict in format { package: {code : the_code}}
        :param tuple position: tuple of the node place
        :param str app_id: app id
        """
        self.name = name
        self.node_id = node_id
        self.outputs = outputs
        self.inputs = inputs
        self.metadata = metadata if metadata is not None else {}
        self.node_type = node_type
        self.namespace = namespace
        self.project_id = project_id
        self.config = config
        self.position = position
        self.app_id = app_id
        self._pipeline = None

    @property
    def position(self):
        position_tuple = (self.metadata['position']['x'],
                          self.metadata['position']['y'])
        return position_tuple

    @position.setter
    def position(self, position):
        self.metadata['position'] = \
            {
                "x": position[0] * 1.7 * NODE_SIZE[0] + NODE_SIZE[0] / 2,
                "y": position[1] * 1.5 * NODE_SIZE[1] + NODE_SIZE[1],
                "z": 0
            }

    def _default_io(self, actions: list = None) -> PipelineNodeIO:
        """
        Create a default item pipeline input

        :param str actions:  the action that move the input when it happen
        :return PipelineNodeIO: the default item PipelineNodeIO
        """
        default_io = PipelineNodeIO(port_id=str(uuid.uuid4()),
                                    input_type=entities.PackageInputType.ITEM,
                                    name='item',
                                    color=None,
                                    display_name=actions[0] if actions else 'item',
                                    actions=actions)
        return default_io

    @staticmethod
    def from_json(_json: dict):
        inputs = [PipelineNodeIO.from_json(_json=i_input) for i_input in _json.get('inputs', list())]
        outputs = [PipelineNodeIO.from_json(_json=i_output) for i_output in _json.get('outputs', list())]
        namespace = PipelineNameSpace.from_json(_json.get('namespace', {}))
        metadata = _json.get('metadata', {})
        position = ((metadata['position']['x'] - NODE_SIZE[0] / 2) / (1.7 * NODE_SIZE[0]),
                    (metadata['position']['y'] - NODE_SIZE[1]) / (1.5 * NODE_SIZE[1]))
        return PipelineNode(
            name=_json.get('name', None),
            node_id=_json.get('id', None),
            outputs=outputs,
            inputs=inputs,
            metadata=metadata,
            node_type=_json.get('type', None),
            namespace=namespace,
            project_id=_json.get('projectId', None),
            config=_json.get('config', None),
            position=position,
            app_id=_json.get('appId', None)
        )

    def to_json(self):
        _json = {
            'name': self.name,
            'id': self.node_id,
            'outputs': [_io.to_json() for _io in self.outputs],
            'inputs': [_io.to_json() for _io in self.inputs],
            'metadata': self.metadata,
            'type': self.node_type,
            'namespace': self.namespace.to_json(),
            'projectId': self.project_id,
        }
        if self.config is not None:
            _json['config'] = self.config
        if self.app_id is not None:
            _json['appId'] = self.app_id
        return _json

    def is_root(self):
        if self._pipeline is not None:
            for node in self._pipeline.start_nodes:
                if self.node_id == node.get('nodeId', None) and node.get('type', None) == 'root':
                    return True
        return False

    def _build_connection(self,
                          node,
                          source_port: PipelineNodeIO = None,
                          target_port: PipelineNodeIO = None,
                          filters: entities.Filters = None,
                          action: str = None) -> PipelineConnection:
        """
        Build connection between the current node and the target node use the given ports

        :param PipelineNode node: the node to connect to it
        :param PipelineNodeIO source_port: the source PipelineNodeIO input port
        :param PipelineNodeIO target_port: the target PipelineNodeIO output port
        :param entities.Filters filters: condition for the connection between the nodes
        :param str action:  the action that move the input when it happen
        :return: the connection between the nodes
        """
        if source_port is None and self.outputs:
            source_port = self.outputs[0]

        if target_port is None and node.inputs:
            target_port = node.inputs[0]

        if node.is_root():
            self._pipeline.set_start_node(self)

        source_connection = PipelineConnectionPort(node_id=self.node_id, port_id=source_port.port_id)
        target_connection = PipelineConnectionPort(node_id=node.node_id, port_id=target_port.port_id)
        if action is None and source_port.actions is not None and source_port.actions != []:
            action = source_port.actions[0]
        connection = PipelineConnection(source=source_connection, target=target_connection, filters=filters,
                                        action=action)
        return connection

    def connect(self,
                node,
                source_port: PipelineNodeIO = None,
                target_port: PipelineNodeIO = None,
                filters=None,
                action: str = None):
        """
        Build connection between the current node and the target node use the given ports

        :param PipelineNode node: the node to connect to it
        :param PipelineNodeIO source_port: the source PipelineNodeIO input port
        :param PipelineNodeIO target_port: the target PipelineNodeIO output port
        :param entities.Filters filters: condition for the connection between the nodes
        :param str action:  the action that move the input when it happen
        :return: the connected node
        """
        if self._pipeline is None:
            raise Exception("must add the node to the pipeline first, e.g pipeline.nodes.add(node)")
        connection = self._build_connection(node=node,
                                            source_port=source_port,
                                            target_port=target_port,
                                            filters=filters,
                                            action=action)
        self._pipeline.connections.append(connection)
        self._pipeline.nodes.add(node)
        return node

    def disconnect(self,
                   node,
                   source_port: PipelineNodeIO = None,
                   target_port: PipelineNodeIO = None) -> bool:
        """
        remove connection between the current node and the target node use the given ports

        :param PipelineNode node: the node to connect to it
        :param PipelineNodeIO source_port: the source PipelineNodeIO input port
        :param PipelineNodeIO target_port: the target PipelineNodeIO output port
        :return: true if success and false if not
        """
        if self._pipeline is None:
            raise Exception("must add the node to the pipeline first, e.g pipeline.nodes.add(node)")
        connection = self._build_connection(node=node,
                                            source_port=source_port,
                                            target_port=target_port,
                                            filters=None)

        current_connection = connection.to_json()
        if 'condition' in current_connection:
            current_connection = current_connection.pop('condition')

        for connection_index in range(len(self._pipeline.connections)):
            pipeline_connection = self._pipeline.connections[connection_index].to_json()
            if 'condition' in pipeline_connection:
                pipeline_connection = pipeline_connection.pop('condition')

            if current_connection == pipeline_connection:
                self._pipeline.connections.pop(connection_index)
                return True
        logger.warning('do not found a connection')
        return False

    def add_trigger(self,
                    trigger_type: entities.TriggerType = entities.TriggerType.EVENT,
                    filters=None,
                    resource: entities.TriggerResource = entities.TriggerResource.ITEM,
                    actions: entities.TriggerAction = entities.TriggerAction.CREATED,
                    execution_mode: entities.TriggerExecutionMode = entities.TriggerExecutionMode.ONCE,
                    cron: str = None,
                    ):
        """
        Create a Trigger. Can create two types: a cron trigger or an event trigger.
        Inputs are different for each type

        Inputs for all types:

        :param trigger_type: can be cron or event. use enum dl.TriggerType for the full list

        Inputs for event trigger:
        :param filters: optional - Item/Annotation metadata filters, default = none
        :param resource: optional - Dataset/Item/Annotation/ItemStatus, default = Item
        :param actions: optional - Created/Updated/Deleted, default = create
        :param execution_mode: how many time trigger should be activate. default is "Once". enum dl.TriggerExecutionMode

        Inputs for cron trigger:
        :param str cron: cron spec specifying when it should run. more information: https://en.wikipedia.org/wiki/Cron

        :return: Trigger entity
        """
        if self._pipeline is None:
            raise Exception("must add the node to the pipeline first, e.g pipeline.nodes.add(node)")

        if not isinstance(actions, list):
            actions = [actions]

        if filters is None:
            filters = {}
        else:
            filters = json.dumps(filters.prepare(query_only=True).get('filter', dict()))

        if trigger_type == entities.TriggerType.EVENT:
            spec = {
                'filter': filters,
                'resource': resource,
                'executionMode': execution_mode,
                'actions': actions
            }
        elif trigger_type == entities.TriggerType.CRON:
            spec = {
                'cron': cron,
            }
        else:
            raise ValueError('Unknown trigger type: "{}". Use dl.TriggerType for known types'.format(trigger_type))

        trigger = {
            "type": trigger_type,
            "spec": spec
        }

        set_trigger = False
        for pipe_node in self._pipeline.start_nodes:
            if pipe_node['nodeId'] == self.node_id:
                set_trigger = True
                pipe_node['trigger'] = trigger

        if not set_trigger:
            self._pipeline.start_nodes.append(
                {
                    "nodeId": self.node_id,
                    "type": "trigger",
                    'trigger': trigger
                }
            )


class CodeNode(PipelineNode):
    def __init__(self,
                 name: str,
                 project_id: str,
                 project_name: str,
                 method: Callable,
                 outputs: List[PipelineNodeIO] = None,
                 inputs: List[PipelineNodeIO] = None,
                 position: tuple = (1, 1),
                 ):
        """
        :param str name: node name
        :param str project_id: project id
        :param str project_name: project name
        :param Callable method: function to deploy
        :param list outputs: list of PipelineNodeIO outputs
        :param list inputs: list of PipelineNodeIO inputs
        :param tuple position: tuple of the node place
        """
        if inputs is None:
            inputs = [self._default_io()]
        if outputs is None:
            outputs = [self._default_io()]

        if method is None or not isinstance(method, Callable):
            raise Exception('must provide a function as input')
        else:
            function_code = self._build_code_from_func(method)
            function_name = method.__name__

        super().__init__(name=name,
                         node_id=str(uuid.uuid4()),
                         outputs=outputs,
                         inputs=inputs,
                         metadata={},
                         node_type=PipelineNodeType.CODE,
                         namespace=PipelineNameSpace(function_name=function_name, project_name=project_name),
                         project_id=project_id,
                         position=position)

        self.config = {
            "package":
                {
                    "code": function_code,
                    "name": function_name,
                    "type": "code"
                }
        }

    def _build_code_from_func(self, func: Callable) -> str:
        """
        Build a code format from the given function

        :param Callable func: function to deploy
        :return: a string the display the code with the package format
        """
        with open(assets.paths.PARTIAL_MAIN_FILEPATH, 'r') as f:
            main_string = f.read()
        lines = inspect.getsourcelines(func)

        tabs_diff = lines[0][0].count('    ') - 1
        for line_index in range(len(lines[0])):
            line_tabs = lines[0][line_index].count('    ') - tabs_diff
            lines[0][line_index] = ('    ' * line_tabs) + lines[0][line_index].strip() + '\n'

        method_func_string = "".join(lines[0])

        code = '{}\n{}\n    @staticmethod\n{}'.format('', main_string,
                                                      method_func_string)
        return code

    @staticmethod
    def from_json(_json: dict):
        parent = PipelineNode.from_json(_json)
        parent.__class__ = CodeNode
        return parent


class TaskNode(PipelineNode):
    def __init__(self,
                 name: str,
                 project_id: str,
                 dataset_id: str,
                 recipe_title: str,
                 recipe_id: str,
                 task_owner: str,
                 workload: List[entities.WorkloadUnit],
                 task_type: str = 'annotation',
                 position: tuple = (1, 1),
                 actions: list = None,
                 repeatable: bool = True,
                 batch_size=None,
                 max_batch_workload=None,
                 priority=entities.TaskPriority.MEDIUM,
                 due_date=None,
                 consensus_task_type=None,
                 consensus_percentage=None,
                 consensus_assignees=None,
                 groups=None
                 ):
        """
        :param str name: node name
        :param str project_id: project id
        :param str dataset_id: dataset id
        :param str recipe_title: recipe title
        :param str recipe_id: recipe id
        :param str task_owner: email of task owner
        :param List[WorkloadUnit] workload: list of WorkloadUnit
        :param str task_type: 'annotation' or 'qa'
        :param tuple position: tuple of the node place
        :param list actions: list of task actions
        :param bool repeatable: can repeat in the item
        :param int groups: groups to assign the task to
        :param int batch_size: Pulling batch size (items) . Restrictions - Min 3, max 100 - for create pulling task
        :param int max_batch_workload: Max items in assignment . Restrictions - Min batchSize + 2 , max batchSize * 2 - for create pulling task
        :param entities.TaskPriority priority: priority of the task options in entities.TaskPriority
        :param float due_date: date by which the task should be finished; for example, due_date = datetime.datetime(day= 1, month= 1, year= 2029).timestamp()
        :param entities.ConsensusTaskType consensus_task_type: consensus_task_type of the task options in entities.ConsensusTaskType
        :param int consensus_percentage: percentage of items to be copied to multiple annotators (consensus items)
        :param int consensus_assignees: the number of different annotators per item (number of copies per item)
        """
        if actions is None or actions == []:
            actions = []
            if task_type == 'qa':
                if 'approve' not in actions:
                    actions.append('approve')
            else:
                if 'complete' not in actions:
                    actions.append('complete')
            actions.append('discard')
        else:
            logger.warning(
                "The 'actions' field was updated to override the system default actions for task (complete/approve, discard) if provided, due to a bug fix.")

        inputs = [self._default_io()]

        outputs = [self._default_io(actions=actions)]

        if groups is not None:
            if not isinstance(groups, list) or not all(isinstance(group, str) for group in groups):
                raise ValueError('groups must be a list of strings')

        super().__init__(name=name,
                         node_id=str(uuid.uuid4()),
                         outputs=outputs,
                         inputs=inputs,
                         metadata=dict(),
                         node_type=PipelineNodeType.TASK,
                         namespace=PipelineNameSpace(function_name="move_to_task",
                                                     project_name="DataloopTasks",
                                                     service_name="pipeline-utils"),
                         project_id=project_id,
                         position=position)

        self.dataset_id = dataset_id
        self.recipe_title = recipe_title
        self.recipe_id = recipe_id
        self.task_owner = task_owner
        self.task_type = task_type
        if not isinstance(workload, list):
            workload = [workload]
        self.workload = workload
        self.repeatable = repeatable
        if max_batch_workload:
            self.max_batch_workload = max_batch_workload
        if batch_size:
            self.batch_size = batch_size
        if consensus_task_type:
            self.consensus_task_type = consensus_task_type
        if consensus_percentage:
            self.consensus_percentage = consensus_percentage
        if consensus_assignees:
            self.consensus_assignees = consensus_assignees
        self.priority = priority
        if due_date is None:
            due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp() * 1000
        self.due_date = due_date
        self.groups = groups

    @property
    def dataset_id(self):
        return self.metadata['datasetId']

    @dataset_id.setter
    def dataset_id(self, dataset_id: str):
        if not isinstance(dataset_id, str):
            raise PlatformException('400', 'Param dataset_id must be of type string')
        self.metadata['datasetId'] = dataset_id

    @property
    def groups(self):
        return self.metadata.get('groups')

    @groups.setter
    def groups(self, groups: List[str]):
        if groups is not None:
            self.metadata['groups'] = groups

    @property
    def repeatable(self):
        return self.metadata['repeatable']

    @repeatable.setter
    def repeatable(self, repeatable: bool):
        if not isinstance(repeatable, bool):
            raise PlatformException('400', 'Param repeatable must be of type bool')
        self.metadata['repeatable'] = repeatable

    @property
    def recipe_title(self):
        return self.metadata['recipeTitle']

    @recipe_title.setter
    def recipe_title(self, recipe_title: str):
        if not isinstance(recipe_title, str):
            raise PlatformException('400', 'Param recipe_title must be of type string')
        self.metadata['recipeTitle'] = recipe_title

    @property
    def recipe_id(self):
        return self.metadata['recipeId']

    @recipe_id.setter
    def recipe_id(self, recipe_id: str):
        if not isinstance(recipe_id, str):
            raise PlatformException('400', 'Param recipe_id must be of type string')
        self.metadata['recipeId'] = recipe_id

    @property
    def task_owner(self):
        return self.metadata['taskOwner']

    @task_owner.setter
    def task_owner(self, task_owner: str):
        if not isinstance(task_owner, str):
            raise PlatformException('400', 'Param task_owner must be of type string')
        self.metadata['taskOwner'] = task_owner

    @property
    def task_type(self):
        return self.metadata['taskType']

    @task_type.setter
    def task_type(self, task_type: str):
        if not isinstance(task_type, str):
            raise PlatformException('400', 'Param task_type must be of type string')
        self.metadata['taskType'] = task_type

    @property
    def workload(self):
        return self.metadata['workload']

    @workload.setter
    def workload(self, workload: list):
        if not isinstance(workload, list):
            workload = [workload]
        self.metadata['workload'] = [val.to_json() for val in workload]

    @property
    def batch_size(self):
        return self.metadata['batchSize']

    @batch_size.setter
    def batch_size(self, batch_size: int):
        if not isinstance(batch_size, int):
            raise PlatformException('400', 'Param batch_size must be of type int')
        self.metadata['batchSize'] = batch_size

    @property
    def max_batch_workload(self):
        return self.metadata['maxBatchWorkload']

    @max_batch_workload.setter
    def max_batch_workload(self, max_batch_workload: int):
        if not isinstance(max_batch_workload, int):
            raise PlatformException('400', 'Param max_batch_workload must be of type int')
        self.metadata['maxBatchWorkload'] = max_batch_workload

    @property
    def consensus_task_type(self):
        return self.metadata['consensusTaskType']

    @consensus_task_type.setter
    def consensus_task_type(self, consensus_task_type: entities.ConsensusTaskType):
        if not isinstance(consensus_task_type, str) and not isinstance(consensus_task_type, entities.ConsensusTaskType):
            raise PlatformException('400', 'Param consensus_task_type must be of type entities.ConsensusTaskType')
        self.metadata['consensusTaskType'] = consensus_task_type

    @property
    def consensus_percentage(self):
        return self.metadata['consensusPercentage']

    @consensus_percentage.setter
    def consensus_percentage(self, consensus_percentage: int):
        if not isinstance(consensus_percentage, int):
            raise PlatformException('400', 'Param consensus_percentage must be of type int')
        self.metadata['consensusPercentage'] = consensus_percentage

    @property
    def consensus_assignees(self):
        return self.metadata['consensusAssignees']

    @consensus_assignees.setter
    def consensus_assignees(self, consensus_assignees: int):
        if not isinstance(consensus_assignees, int):
            raise PlatformException('400', 'Param consensus_assignees must be of type int')
        self.metadata['consensusAssignees'] = consensus_assignees

    @property
    def priority(self):
        return self.metadata['priority']

    @priority.setter
    def priority(self, priority: entities.TaskPriority):
        if not isinstance(priority, int) and not isinstance(priority, entities.TaskPriority):
            raise PlatformException('400', 'Param priority must be of type entities.TaskPriority')
        self.metadata['priority'] = priority

    @property
    def due_date(self):
        return self.metadata['dueDate']

    @due_date.setter
    def due_date(self, due_date: float):
        if not isinstance(due_date, float) and not isinstance(due_date, int):
            raise PlatformException('400', 'Param due_date must be of type float or int')
        self.metadata['dueDate'] = due_date

    @staticmethod
    def from_json(_json: dict):
        parent = PipelineNode.from_json(_json)
        parent.__class__ = TaskNode
        return parent


class FunctionNode(PipelineNode):
    def __init__(self,
                 name: str,
                 service: entities.Service,
                 function_name,
                 position: tuple = (1, 1),
                 project_id=None,
                 project_name=None
                 ):
        """
        :param str name: node name
        :param entities.Service service: service to deploy
        :param str function_name: function name
        :param tuple position: tuple of the node place
        """
        self.service = service

        if project_id is None:
            project_id = service.project_id
        if project_id != service.project_id:
            logger.warning("the project id that provide different from the service project id")

        if project_name is None:
            try:
                project = repositories.Projects(client_api=self.service._client_api).get(project_id=project_id,
                                                                                         log_error=False)
                project_name = project.name
            except:
                logger.warning(
                    'Service project not found using DataloopTasks project.'
                    ' If this is incorrect please provide project_name param.')
                project_name = 'DataloopTasks'
        inputs = []
        outputs = []
        package = self.service.package
        modules = []
        if isinstance(package, entities.Package):
            modules = package.modules
        elif isinstance(package, entities.Dpk):
            modules = package.components.modules
        for model in modules:
            if model.name == self.service.module_name:
                for func in model.functions:
                    if func.name == function_name:
                        inputs = self._convert_from_function_io_to_pipeline_io(func.inputs)
                        outputs = self._convert_from_function_io_to_pipeline_io(func.outputs)

        namespace = PipelineNameSpace(
            function_name=function_name,
            service_name=self.service.name,
            module_name=self.service.module_name,
            package_name=self.service.package.name,
            project_name=project_name
        )
        super().__init__(name=name,
                         node_id=str(uuid.uuid4()),
                         outputs=outputs,
                         inputs=inputs,
                         metadata={},
                         node_type=PipelineNodeType.FUNCTION,
                         namespace=namespace,
                         project_id=service.project_id,
                         position=position)

    def _convert_from_function_io_to_pipeline_io(self, function_io: List[entities.FunctionIO]) -> List[PipelineNodeIO]:
        """
        Get a list of FunctionIO and convert them to PipelineIO
        :param List[entities.FunctionIO] function_io: list of functionIO
        :return: list of PipelineIO
        """
        pipeline_io = []
        for single_input in function_io:
            pipeline_io.append(
                PipelineNodeIO(port_id=str(uuid.uuid4()),
                               input_type=single_input.type,
                               name=single_input.name,
                               color=None,
                               display_name=single_input.name,
                               default_value=single_input.value,
                               actions=single_input.actions if single_input.actions is not None else []))
        return pipeline_io

    @staticmethod
    def from_json(_json: dict):
        parent = PipelineNode.from_json(_json)
        parent.__class__ = FunctionNode
        return parent


class DatasetNode(PipelineNode):
    def __init__(self,
                 name: str,
                 project_id: str,
                 dataset_id: str,
                 dataset_folder: str = None,
                 position: tuple = (1, 1)):
        """
        :param str name: node name
        :param str project_id: project id
        :param str dataset_id: dataset id
        :param str dataset_folder: folder in dataset to work in it
        :param tuple position: tuple of the node place
        """
        inputs = [self._default_io()]
        outputs = [self._default_io()]
        super().__init__(name=name,
                         node_id=str(uuid.uuid4()),
                         outputs=outputs,
                         inputs=inputs,
                         metadata={},
                         node_type=PipelineNodeType.STORAGE,
                         namespace=PipelineNameSpace(function_name="dataset_handler",
                                                     project_name="DataloopTasks",
                                                     service_name="pipeline-utils"),
                         project_id=project_id,
                         position=position)
        self.dataset_id = dataset_id
        self.dataset_folder = dataset_folder

    @property
    def dataset_id(self):
        return self.metadata['datasetId']

    @dataset_id.setter
    def dataset_id(self, dataset_id: str):
        self.metadata['datasetId'] = dataset_id

    @property
    def dataset_folder(self):
        return self.metadata.get('dir', None)

    @dataset_folder.setter
    def dataset_folder(self, dataset_folder: str):
        if dataset_folder is not None:
            if not dataset_folder.startswith("/"):
                dataset_folder = '/' + dataset_folder
            self.metadata['dir'] = dataset_folder

    @staticmethod
    def from_json(_json: dict):
        parent = PipelineNode.from_json(_json)
        parent.__class__ = DatasetNode
        return parent
