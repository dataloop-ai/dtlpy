import attr
import traceback
import logging
from enum import Enum
from collections import namedtuple

from .. import entities, exceptions, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class TriggerResource(str, Enum):
    ITEM = "Item"
    DATASET = "Dataset"
    ANNOTATION = "Annotation"
    TASK = 'Task',
    ASSIGNMENT = 'Assignment',
    ITEM_STATUS = "ItemStatus"


class TriggerAction(str, Enum):
    CREATED = "Created"
    UPDATED = "Updated"
    DELETED = "Deleted"
    STATUS_CHANGED = 'statusChanged'
    CLONE = 'Clone'


class TriggerExecutionMode(str, Enum):
    ONCE = "Once"
    ALWAYS = "Always"


class TriggerType(str, Enum):
    EVENT = "Event"
    CRON = "Cron"


@attr.s
class BaseTrigger(entities.BaseEntity):
    """
    Trigger Entity
    """
    #######################
    # Platform attributes #
    #######################
    id = attr.ib()
    url = attr.ib(repr=False)
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    creator = attr.ib()
    name = attr.ib()
    active = attr.ib()
    type = attr.ib()
    scope = attr.ib()
    is_global = attr.ib()
    input = attr.ib()

    # name change
    function_name = attr.ib()
    service_id = attr.ib()
    webhook_id = attr.ib()
    pipeline_id = attr.ib()

    ########
    # temp #
    ########
    special = attr.ib(repr=False)

    ##############################
    # different name in platform #
    ##############################
    project_id = attr.ib()
    _spec = attr.ib()
    operation = attr.ib()

    ##################
    # SDK attributes #
    ##################
    _service = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _op_type = attr.ib(default='service')
    _repositories = attr.ib(repr=False)

    updated_by = attr.ib(default=None)

    @staticmethod
    def _get_operation(operation):
        op_type = operation.get('type', None)
        if op_type == 'function':
            service_id = operation.get('serviceId', None)
            webhook_id = None
            pipeline_id = None
        elif op_type == 'webhook':
            webhook_id = operation.get('webhookId', None)
            service_id = None
            pipeline_id = None
        elif op_type == 'rabbitmq':
            webhook_id = None
            service_id = None
            pipeline_id = None
        elif op_type == 'pipeline':
            webhook_id = None
            service_id = None
            pipeline_id = operation.get('id', None)
        else:
            raise exceptions.PlatformException('400', 'unknown trigger operation type: {}'.format(op_type))

        return service_id, webhook_id, pipeline_id

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @staticmethod
    def _protected_from_json(_json, client_api, project=None, service=None):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :param service: service entity
        :return:
        """
        try:
            trigger = BaseTrigger.from_json(_json=_json,
                                            client_api=client_api,
                                            project=project,
                                            service=service)
            status = True
        except Exception:
            trigger = traceback.format_exc()
            status = False
        return status, trigger

    @classmethod
    def from_json(cls, _json, client_api, project=None, service=None):
        """
        Build a trigger entity object from a json

        :param dict _json: platform json
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.project.Project project: project entity
        :param dtlpy.entities.service.Service service: service entity
        :return:
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Trigger has been fetched from a project that is not belong to it')
                project = None

        if service is not None:
            spec = _json.get('spec', dict())
            operation = spec.get('operation', dict())
            if service.id != operation.get('serviceId', None):
                logger.warning('Trigger has been fetched from a service that is not belong to it')
                service = None

        trigger_type = _json.get('type', None)

        if trigger_type == TriggerType.CRON:
            ent = CronTrigger.from_json(_json, client_api, project, service)
        else:
            ent = Trigger.from_json(_json, client_api, project, service)
        return ent

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['services', 'triggers'])

        if self._project is None:
            services_repo = repositories.Services(client_api=self._client_api, project=self._project)
        else:
            services_repo = self._project.services

        triggers = repositories.Triggers(client_api=self._client_api,
                                         project=self._project)

        r = reps(services=services_repo, triggers=triggers)
        return r

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def service(self):
        if self._service is None:
            self._service = self.services.get(service_id=self.service_id, fetch=None)
        assert isinstance(self._service, entities.Service)
        return self._service

    ###########
    # methods #
    ###########
    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(BaseTrigger)._client_api,
                                                              attr.fields(BaseTrigger).project_id,
                                                              attr.fields(BaseTrigger)._project,
                                                              attr.fields(BaseTrigger)._service,
                                                              attr.fields(BaseTrigger).special,
                                                              attr.fields(BaseTrigger)._op_type,
                                                              attr.fields(BaseTrigger)._spec,
                                                              attr.fields(BaseTrigger)._repositories,
                                                              attr.fields(BaseTrigger).service_id,
                                                              attr.fields(BaseTrigger).webhook_id,
                                                              attr.fields(BaseTrigger).pipeline_id,
                                                              attr.fields(BaseTrigger).function_name,
                                                              attr.fields(BaseTrigger).is_global,
                                                              attr.fields(BaseTrigger).created_at,
                                                              attr.fields(BaseTrigger).updated_at,
                                                              attr.fields(BaseTrigger).operation,
                                                              attr.fields(BaseTrigger).updated_by,
                                                              ))

        # rename
        _json['projectId'] = self.project_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        if self.is_global is not None:
            _json['global'] = self.is_global
        if self.updated_by is not None:
            _json['updatedBy'] = self.updated_by
        return _json

    def delete(self):
        """
        Delete Trigger object

        :return: True
        """
        return self.project.triggers.delete(trigger_id=self.id)

    def update(self):
        """
        Update Trigger object

        :return: Trigger entity
        """
        return self.project.triggers.update(trigger=self)


@attr.s
class Trigger(BaseTrigger):
    """
    Trigger Entity
    """
    filters = attr.ib(default=None, repr=False)
    execution_mode = attr.ib(default=TriggerExecutionMode.ONCE, repr=False)
    actions = attr.ib(default=TriggerAction.CREATED, repr=False)
    resource = attr.ib(default=TriggerResource.ITEM, repr=False)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = super().to_json()

        _json['spec'] = {
            'filter': _json.pop('filters'),
            'executionMode': _json.pop('execution_mode'),
            'resource': _json.pop('resource'),
            'actions': _json.pop('actions'),
            'input': _json.pop('input', None),
            'operation': self.operation,
        }
        return _json

    @classmethod
    def from_json(cls, _json, client_api, project=None, service=None):
        """
        Build a trigger entity object from a json

        :param _json: platform json
        :param client_api: ApiClient entity
        :param dtlpy.entities.project.Project project: project entity
        :param dtlpy.entities.service.Service service: service entity
        :return:
        """
        spec = _json.get('spec', dict())
        operation = spec.get('operation', dict())

        service_id, webhook_id, pipeline_id = cls._get_operation(operation=operation)

        return cls(
            execution_mode=spec.get('executionMode', None),
            updated_at=_json.get('updatedAt', None),
            created_at=_json.get('createdAt', None),
            resource=spec.get('resource', None),
            creator=_json.get('creator', None),
            special=_json.get('special', None),
            actions=spec.get('actions', None),
            active=_json.get('active', None),
            function_name=operation.get('functionName', None),
            scope=_json.get('scope', None),
            is_global=_json.get('global', None),
            type=_json.get('type', None),
            name=_json.get('name', None),
            url=_json.get('url', None),
            service_id=service_id,
            project_id=_json.get('projectId', None),
            input=spec.get('input', None),
            webhook_id=webhook_id,
            client_api=client_api,
            filters=spec.get('filter', dict()),
            project=project,
            service=service,
            id=_json['id'],
            op_type=operation.get('type', None),
            spec=spec,
            pipeline_id=pipeline_id,
            operation=operation,
            updated_by=_json.get('updatedBy', None),
        )


@attr.s
class CronTrigger(BaseTrigger):
    start_at = attr.ib(default=None)
    end_at = attr.ib(default=None)
    cron = attr.ib(default=None)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = super().to_json()

        _json['spec'] = {
            'startAt': _json.pop('start_at'),
            'endAt': _json.pop('end_at'),
            'cron': _json.pop('cron'),
            'input': _json.pop('input'),
            'operation': self.operation,
        }
        return _json

    @classmethod
    def from_json(cls, _json, client_api, project=None, service=None):
        """
        Build a trigger entity object from a json

        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :param service: service entity
        :return:
        """
        spec = _json.get('spec', dict())
        operation = spec.get('operation', dict())

        project_id = _json.get('projectId', None)
        if project_id is not None and project is not None:
            if project_id != project.id:
                project = None

        service_id, webhook_id, pipeline_id = cls._get_operation(operation=operation)
        return cls(
            updated_at=_json.get('updatedAt', None),
            created_at=_json.get('createdAt', None),
            creator=_json.get('creator', None),
            special=_json.get('special', None),
            active=_json.get('active', None),
            function_name=operation.get('functionName', None),
            scope=_json.get('scope', None),
            is_global=_json.get('global', None),
            type=_json.get('type', None),
            name=_json.get('name', None),
            input=spec.get('input', None),
            end_at=spec.get('endAt', None),
            start_at=spec.get('startAt', None),
            cron=spec.get('cron', None),
            url=_json.get('url', None),
            service_id=service_id,
            project_id=project_id,
            webhook_id=webhook_id,
            client_api=client_api,
            project=project,
            service=service,
            id=_json['id'],
            op_type=operation.get('type', None),
            spec=spec,
            pipeline_id=pipeline_id,
            operation=operation
        )
