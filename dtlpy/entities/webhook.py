import logging
import attr

from .. import services, repositories, entities, miscellaneous, exceptions

logger = logging.getLogger("dataloop.service")


@attr.s
class Webhook:
    """
    Webhook object
    """
    # platform
    id = attr.ib()
    url = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()
    name = attr.ib()

    # name change
    project_id = attr.ib()
    http_method = attr.ib()
    hook_url = attr.ib()

    # SDK
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _project = attr.ib()

    # repos
    _webhooks = attr.ib(default=None)

    @classmethod
    def from_json(cls, _json, client_api, project=None):
        return cls(
            http_method=_json.get('httpMethod', None),
            createdAt=_json.get("createdAt", None),
            updatedAt=_json.get("updatedAt", None),
            project_id=_json.get('project', None),
            hook_url=_json.get('hookUrl', None),
            creator=_json.get("creator", None),
            name=_json.get("name", None),
            url=_json.get("url", None),
            id=_json.get("id", None),
            client_api=client_api,
            project=project
        )

    @property
    def project(self):
        if self._project is None:
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    def get_project(self, dummy=False):
        if self._project is None:
            if dummy:
                self._project = entities.Project.dummy(project_id=self.project_id, client_api=self._client_api)
            else:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id)

    @property
    def webhooks(self):
        if self._webhooks is None:
            self._webhooks = repositories.Webhooks(client_api=self._client_api, project=self._project)
        assert isinstance(self._webhooks, repositories.Webhooks)
        return self._webhooks

    def print(self):
        miscellaneous.List([self]).print()

    def to_json(self):
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Webhook)._project,
                attr.fields(Webhook)._client_api,
                attr.fields(Webhook).project_id,
                attr.fields(Webhook).hook_url,
                attr.fields(Webhook).http_method,
            ),
        )

        _json['project'] = self.project_id
        _json['hookUrl'] = self.hook_url
        _json['httpMethod'] = self.http_method

        return _json

    def delete(self):
        return self.webhooks.delete(self)

    def update(self):
        return self.webhooks.update(self)
