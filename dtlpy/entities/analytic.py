import logging
from .. import entities

logger = logging.getLogger(name='dtlpy')


class BaseSample:
    def __init__(self,
                 start_time,
                 end_time,
                 project_id,
                 org_id,
                 pipeline_id,
                 event_type,
                 action,
                 status,
                 ):
        self.start_time = start_time
        self.end_time = end_time
        self.project_id = project_id
        self.org_id = org_id
        self.pipeline_id = pipeline_id
        self.event_type = event_type
        self.action = action
        self.status = status


class ServiceSample(BaseSample):
    def __init__(self,
                 start_time=None,
                 end_time=None,
                 user_id=None,
                 project_id=None,
                 org_id=None,
                 pipeline_id=None,
                 pipeline_node_id=None,
                 service_id=None,
                 pod_id=None,
                 pod_type=None,
                 event_type=None,
                 entity_type=None,
                 action=None,
                 status=None,
                 num_restarts=None,
                 cpu=None,
                 ram=None,
                 queue_size=None,
                 num_executions=None,
                 service_type: entities.ServiceType = None
                 ):
        super().__init__(start_time=start_time,
                         end_time=end_time,
                         project_id=project_id,
                         org_id=org_id,
                         pipeline_id=pipeline_id,
                         event_type=event_type,
                         action=action,
                         status=status)
        self.user_id = user_id
        self.pipeline_node_id = pipeline_node_id
        self.service_id = service_id
        self.pod_id = pod_id
        self.pod_type = pod_type
        self.entity_type = entity_type
        self.num_restarts = num_restarts
        self.cpu = cpu
        self.ram = ram
        self.queue_size = queue_size
        self.num_executions = num_executions
        self.service_type = service_type if service_type is not None else entities.ServiceType.REGULAR

    def to_json(self):
        _json = {
            'startTime': self.start_time,
            'endTime': self.end_time,
            'context': {
                'userId': self.user_id,
                'projectId': self.project_id,
                'projectOrgId': self.org_id,
                'pipelineId': self.pipeline_id,
                'pipelineNodeId': self.pipeline_node_id,
                'serviceId': self.service_id,
                'podId': self.pod_id,
                'podType': self.pod_type,
                'serviceType': self.service_type
            },
            'eventType': self.event_type,
            'entityType': self.entity_type,
            'action': self.action,
            'data': {
                'status': self.status,
                'numRestarts': self.num_restarts,
                'cpu': self.cpu,
                'ram': self.ram,
                'queueSize': self.queue_size,
                'numExecutions': self.num_executions
            }
        }
        _json['context'] = {k: v for k, v in _json['context'].items() if v is not None}
        _json['data'] = {k: v for k, v in _json['data'].items() if v is not None}

        return {k: v for k, v in _json.items() if v is not None}

    @classmethod
    def from_json(cls, _json):
        inst = cls(
            start_time=_json.get('startTime', None),
            end_time=_json.get('endTime', None),
            user_id=_json.get('context', {}).get('userId', None),
            project_id=_json.get('context', {}).get('projectId', None),
            org_id=_json.get('context', {}).get('projectOrgId', None),
            pipeline_id=_json.get('context', {}).get('pipelineId', None),
            pipeline_node_id=_json.get('context', {}).get('pipelineNodeId', None),
            service_id=_json.get('context', {}).get('serviceId', None),
            pod_id=_json.get('context', {}).get('podId', None),
            pod_type=_json.get('context', {}).get('podType', None),
            event_type=_json.get('eventType', None),
            entity_type=_json.get('EntityType', None),
            action=_json.get('action', None),
            status=_json.get('data', {}).get('status', None),
            num_restarts=_json.get('data', {}).get('numRestarts', None),
            cpu=_json.get('data', {}).get('cpu', None),
            ram=_json.get('data', {}).get('ram', None),
            queue_size=_json.get('data', {}).get('queueSize', None),
            num_executions=_json.get('data', {}).get('numExecutions', None),
            service_type=_json.get('type', entities.ServiceType.REGULAR),
        )
        return inst


class ExecutionSample(BaseSample):
    def __init__(self,
                 start_time=None,
                 end_time=None,
                 project_id=None,
                 org_id=None,
                 pipeline_id=None,
                 event_type=None,
                 action=None,
                 status=None,
                 user_id=None,
                 account_id=None,
                 pipeline_node_id=None,
                 pipeline_execution_id=None,
                 service_id=None,
                 execution_id=None,
                 trigger_id=None,
                 function_name=None,
                 duration=None
                 ):
        super().__init__(start_time=start_time,
                         end_time=end_time,
                         project_id=project_id,
                         org_id=org_id,
                         pipeline_id=pipeline_id,
                         event_type=event_type,
                         action=action,
                         status=status)
        self.user_id = user_id
        self.account_id = account_id
        self.pipeline_node_id = pipeline_node_id
        self.pipeline_execution_id = pipeline_execution_id
        self.service_id = service_id
        self.execution_id = execution_id
        self.trigger_id = trigger_id
        self.function_name = function_name
        self.duration = duration

    def to_json(self):
        _json = {
            'startTime': self.start_time,
            'endTime': self.end_time,
            'context': {
                'userId': self.user_id,
                'projectId': self.project_id,
                'projectOrgId': self.org_id,
                'accountId': self.account_id,
                'pipelineId': self.pipeline_id,
                'pipelineNodeId': self.pipeline_node_id,
                'pipelineExecutionId': self.pipeline_execution_id,
                'serviceId': self.service_id,
                'executionId': self.execution_id,
                'triggerId': self.trigger_id,
            },
            'eventType': self.event_type,
            'action': self.action,
            'data': {
                'status': self.status,
                'functionName': self.function_name,
                'duration': self.duration
            }
        }
        return _json

    @classmethod
    def from_json(cls, _json):
        inst = cls(
            start_time=_json.get('startTime', None),
            end_time=_json.get('endTime', None),
            user_id=_json.get('context', {}).get('userId', None),
            project_id=_json.get('context', {}).get('projectId', None),
            org_id=_json.get('context', {}).get('projectOrgId', None),
            account_id=_json.get('context', {}).get('accountId', None),
            pipeline_id=_json.get('context', {}).get('pipelineId', None),
            pipeline_node_id=_json.get('context', {}).get('pipelineNodeId', None),
            pipeline_execution_id=_json.get('context', {}).get('pipelineExecutionId', None),
            service_id=_json.get('context', {}).get('serviceId', None),
            execution_id=_json.get('context', {}).get('pipelineExecutionId', None),
            trigger_id=_json.get('context', {}).get('triggerId', None),
            event_type=_json.get('eventType', None),
            action=_json.get('action', None),
            status=_json.get('data', {}).get('status', None),
            function_name=_json.get('data', {}).get('functionName', None),
            duration=_json.get('data', {}).get('duration', None)
        )
        return inst


class PipelineExecutionSample(BaseSample):
    def __init__(self,
                 start_time=None,
                 end_time=None,
                 project_id=None,
                 org_id=None,
                 pipeline_id=None,
                 event_type=None,
                 action=None,
                 status=None,
                 account_id=None,
                 pipeline_node_id=None,
                 pipeline_execution_id=None,
                 trigger_id=None,
                 node_status=None,
                 ):
        super().__init__(start_time=start_time,
                         end_time=end_time,
                         project_id=project_id,
                         org_id=org_id,
                         pipeline_id=pipeline_id,
                         event_type=event_type,
                         action=action,
                         status=status)
        self.account_id = account_id
        self.pipeline_node_id = pipeline_node_id
        self.pipeline_execution_id = pipeline_execution_id
        self.trigger_id = trigger_id
        self.node_status = node_status

    def to_json(self):
        _json = {
            'startTime': self.start_time,
            'endTime': self.end_time,
            'context': {
                'projectId': self.project_id,
                'projectOrgId': self.org_id,
                'accountId': self.account_id,
                'pipelineId': self.pipeline_id,
                'pipelineExecutionId': self.pipeline_execution_id,
                'triggerId': self.trigger_id,
            },
            'eventType': self.event_type,
            'action': self.action,
            'data': {
                'status': self.status,
                'nodeId': self.pipeline_node_id,
                'nodeStatus': self.node_status
            }
        }
        return _json

    @classmethod
    def from_json(cls, _json):
        inst = cls(
            start_time=_json.get('startTime', None),
            end_time=_json.get('endTime', None),
            project_id=_json.get('context', {}).get('projectId', None),
            org_id=_json.get('context', {}).get('projectOrgId', None),
            account_id=_json.get('context', {}).get('accountId', None),
            pipeline_id=_json.get('context', {}).get('pipelineId', None),
            pipeline_execution_id=_json.get('context', {}).get('pipelineExecutionId', None),
            trigger_id=_json.get('context', {}).get('triggerId', None),
            event_type=_json.get('eventType', None),
            action=_json.get('action', None),
            status=_json.get('data', {}).get('status', None),
            pipeline_node_id=_json.get('data', {}).get('pipelineNodeId', None),
            node_status=_json.get('data', {}).get('nodeStatus', None)
        )
        return inst
