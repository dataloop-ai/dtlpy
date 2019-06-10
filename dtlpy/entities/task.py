import logging
from .. import utilities, repositories
import attr

logger = logging.getLogger('dataloop.pipeline')


@attr.s
class Task:
    """
    Task object
    """
    # platform
    client_api = attr.ib()
    id = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    url = attr.ib()

    # params
    version = attr.ib()
    name = attr.ib()
    triggers = attr.ib()
    input = attr.ib()
    output = attr.ib()
    pipeline = attr.ib()
    revisions = attr.ib()
    metadata = attr.ib()
    triggersFilter = attr.ib()
    description = attr.ib()
    mq_details = attr.ib()
    projects = attr.ib()  # list of projects

    # repositories
    _sessions = attr.ib()

    @_sessions.default
    def set_sessions(self):
        return repositories.Sessions(client_api=self.client_api, task=self)

    @property
    def sessions(self):
        assert isinstance(self._sessions, repositories.Sessions)
        return self._sessions

    @classmethod
    def from_json(cls, _json, client_api):
        """
        Build a Task entity object from a json

        :param _json: _json respons form host
        :param client_api: client_api
        :return: Task object
        """
        return cls(
            client_api=client_api,
            id=_json['id'],
            version=_json['version'],
            creator=_json.get('creator', ''),
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            name=_json['name'],
            triggers=_json.get('triggers', list()),
            input=_json['input'],
            output=_json['output'],
            pipeline=_json['pipeline'],
            revisions=_json['revisions'],
            metadata=_json['metadata'],
            triggersFilter=_json.get('triggersFilter', dict()),
            url=_json['url'],
            description=_json['metadata']['system']['description'],
            mq_details=_json['metadata']['system']['mq'],
            projects=_json['metadata']['system']['projects']
        )

    def print(self):
        utilities.List([self]).print()

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(Task).sessions,
                                                       attr.fields(Task).description,
                                                       attr.fields(Task).mq_details,
                                                       attr.fields(Task).projects))
