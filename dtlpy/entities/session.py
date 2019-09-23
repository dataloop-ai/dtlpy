import attr
from .. import repositories, entities, services


@attr.s
class Session:
    """
    Deployment session entity
    """
    # platform
    id = attr.ib()
    url = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    input = attr.ib()
    output = attr.ib()
    feedbackQueue = attr.ib()
    status = attr.ib()
    triggerId = attr.ib()
    deploymentId = attr.ib()
    syncReplyTo = attr.ib()

    # name changed
    project_id = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient)
    _deployment = attr.ib()

    @classmethod
    def from_json(cls, _json, client_api, deployment=None):

        return cls(
            feedbackQueue=_json.get('feedbackQueue', None),
            deploymentId=_json.get('deploymentId', None),
            syncReplyTo=_json.get('syncReplyTo', None),
            project_id=_json.get('project', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            triggerId=_json.get('triggerId', None),
            output=_json.get('output', None),
            status=_json.get('status', None),
            input=_json.get('input', None),
            url=_json.get('url', None),
            id=_json.get('id', None),
            client_api=client_api,
            deployment=deployment
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Session)._client_api,
                                                              attr.fields(Session).project_id,
                                                              attr.fields(Session)._deployment))
        # rename
        _json['project'] = self.project_id
        return _json

    @property
    def deployment(self):
        if self._deployment is None:
            deployments = repositories.Deployments(client_api=self._client_api)
            self._deployment = deployments.get(deployment_id=self.deploymentId)
        assert isinstance(self._deployment, entities.Deployment)
        return self._deployment

    @deployment.setter
    def deployment(self, deployment):
        assert isinstance(deployment, entities.Deployment)
        self._deployment = deployment

    def progress_update(self, status=None, percent_complete=None, message=None, output=None):
        """
        Update Session Progress

        :param status:
        :param percent_complete:
        :param message:
        :param output:
        :return:
        """
        return self.deployment.sessions.progress_update(session_id=self.id,
                                                        status=status,
                                                        percent_complete=percent_complete,
                                                        message=message,
                                                        output=output)
