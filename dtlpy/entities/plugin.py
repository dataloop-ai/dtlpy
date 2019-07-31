import logging
from .. import utilities, repositories
import attr

logger = logging.getLogger('dataloop.plugin')


@attr.s
class Plugin:
    """
    Plugin object
    """
    client_api = attr.ib()
    id = attr.ib()
    version = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    name = attr.ib()
    input = attr.ib()
    output = attr.ib()
    pipeline = attr.ib()
    revisions = attr.ib()
    metadata = attr.ib()
    url = attr.ib()
    description = attr.ib()
    mq_details = attr.ib()
    projects = attr.ib()
    sessions = attr.ib()

    @sessions.default
    def set_sessions(self):
        return repositories.Sessions(client_api=self.client_api, task=self)

    @classmethod
    def from_json(cls, _json, client_api):
        try:
            description = _json['metadata']['system']['description']
        except KeyError:
            description = ''

        return cls(
            client_api=client_api,
            id=_json['id'],
            version=_json['version'],
            creator=_json.get('creator', ''),
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            name=_json['name'],
            input=_json['input'],
            output=_json['output'],
            pipeline=_json['pipeline'],
            revisions=_json['revisions'],
            metadata=_json['metadata'],
            url=_json['url'],
            description=description,
            mq_details=_json['metadata']['system']['mq'],
            projects=_json['metadata']['system']['projects']
        )

    def print(self):
        utilities.List([self]).print()

    def to_json(self):
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(Plugin).sessions,
                                                       attr.fields(Plugin).description,
                                                       attr.fields(Plugin).mq_details,
                                                       attr.fields(Plugin).projects,
                                                       attr.fields(Plugin).client_api))


@attr.s
class PluginInput:
    path = attr.ib()
    resource = attr.ib()
    by = attr.ib()
    constValue = attr.ib()

    def to_json(self):
        return attr.asdict(self)


@attr.s
class PluginOutput:
    name = attr.ib()
    type = attr.ib()
    value = attr.ib()

    def to_json(self):
        return attr.asdict(self)
