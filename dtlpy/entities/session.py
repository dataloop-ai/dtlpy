import logging
from .. import utilities
import attr

logger = logging.getLogger('dataloop.package')


@attr.s
class Session:
    """
    Session object
    """
    # platform
    id = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    url = attr.ib()
    taskId = attr.ib()

    # params
    input = attr.ib()
    output = attr.ib()
    error = attr.ib()
    feedbackQueue = attr.ib()
    status = attr.ib()
    metadata = attr.ib()
    latestStatus = attr.ib()
    reporting_exchange = attr.ib()
    reporting_route = attr.ib()

    # entities
    task = attr.ib()

    @classmethod
    def from_json(cls, _json, task):
        """
        Build a Session entity object from a json

        :param _json: _json respons form host
        :param task: session's task
        :return: Session object
        """
        return cls(
            task=task,
            id=_json['id'],
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            input=_json['input'],
            output=_json.get('output', list()),
            error=_json.get('error', str()),
            feedbackQueue=_json['feedbackQueue'],
            status=_json['status'],
            metadata=_json['metadata'],
            latestStatus=_json['latestStatus'],
            url=_json['url'],
            taskId=_json['metadata']['system']['taskId'],
            reporting_exchange=_json['feedbackQueue']['exchange'],
            reporting_route=_json['feedbackQueue']['routing']
        )

    def print(self):
        utilities.List([self]).print()

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(Session).taskId,
                                                       attr.fields(Session).reporting_exchange,
                                                       attr.fields(Session).reporting_route))
