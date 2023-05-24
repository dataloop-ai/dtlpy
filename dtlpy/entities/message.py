import traceback
import logging
import attr
from .. import repositories, entities
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class NotificationEventContext:

    def __init__(self, context: dict):
        self.project: str = context.get('project', None)
        self.org: str = context.get('org', None)
        self.pipeline: str = context.get('pipeline', None)
        self.service: str = context.get('service', None)
        self.node: str = context.get('node', None)

    @classmethod
    def from_json(cls, _json: dict):
        return cls(context=_json)

    def to_json(self):
        _json = dict()
        if self.project:
            _json['project'] = self.project
        if self.org:
            _json['org'] = self.org
        if self.pipeline:
            _json['pipeline'] = self.pipeline
        if self.service:
            _json['service'] = self.service
        if self.node:
            _json['node'] = self.node
        return _json


@attr.s
class Message(entities.BaseEntity):
    """
    Message object
    """
    title = attr.ib(type=str)
    description = attr.ib(type=str)
    context = attr.ib(type=NotificationEventContext)
    read = attr.ib(type=int)
    dismissed = attr.ib(type=int)
    new = attr.ib(type=int)

    # from camel case to snake case
    user_id = attr.ib(type=str)
    notification_id = attr.ib(type=str)
    resource_action = attr.ib(type=str)
    notification_code = attr.ib(type=str)
    resource_type = attr.ib(type=str)
    resource_id = attr.ib(type=str)
    resource_name = attr.ib(type=str)

    # api
    _client_api = attr.ib(type=ApiClient, repr=False)

    # entities
    _project = attr.ib(default=None, repr=False)

    @staticmethod
    def _protected_from_json(
            _json: dict,
            client_api: ApiClient,
            project: entities.Project = None,
            is_fetched=True
    ):
        """
        Same as from_json but with try-except to catch if error

        :param project: message's project
        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Message object
        """
        try:
            message = Message.from_json(project=project,
                                        _json=_json,
                                        client_api=client_api,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            message = traceback.format_exc()
            status = False
        return status, message

    @classmethod
    def from_json(cls,
                  _json: dict,
                  client_api: ApiClient,
                  project: entities.Project = None,
                  is_fetched=True
                  ):
        """
        Build a Message entity object from a json

        :param project: message's project
        :param dict _json: _json response from host
        :param client_api: ApiClient entityÏ
        :param bool is_fetched: is Entity fetched from Platform
        :return: Dataset object
        :rtype: dtlpy.entities.message.Message
        """

        inst = cls(
            title=_json.get('title', None),
            description=_json.get('description', None),
            context=NotificationEventContext.from_json(_json=_json.get('context', None)),
            read=_json.get('read', None),
            dismissed=_json.get('dismissed', None),
            new=_json.get('new', None),
            user_id=_json.get('userId', None),
            notification_id=_json.get('notificationId', None),
            resource_action=_json.get('resourceAction', None),
            notification_code=_json.get('notificationCode', None),
            resource_type=_json.get('resourceType', None),
            resource_id=_json.get('resourceId', None),
            resource_name=_json.get('resourceName', None),
            client_api=client_api,
            project=project
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(
            self, filter=attr.filters.exclude(
                attr.fields(Message)._client_api,
                attr.fields(Message)._project,
                attr.fields(Message).is_fetched,
                attr.fields(Message).context,
                attr.fields(Message).user_id,
                attr.fields(Message).notification_id,
                attr.fields(Message).resource_action,
                attr.fields(Message).notification_code,
                attr.fields(Message).resource_type,
                attr.fields(Message).resource_id,
                attr.fields(Message).resource_name
            )
        )

        _json['context'] = self.context.to_json()
        _json['userId'] = self.user_id
        _json['notificationId'] = self.notification_id
        _json['resourceAction'] = self.resource_action
        _json['notificationCode'] = self.notification_code
        _json['resourceType'] = self.resource_type
        _json['resourceId'] = self.resource_id
        _json['resourceName'] = self.resource_name

        return _json

    @property
    def project(self):
        if self._project is None and self.context.project is not None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.context.project)
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project
