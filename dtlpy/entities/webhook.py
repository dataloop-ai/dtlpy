import logging
import attr

from .. import services, repositories, entities

logger = logging.getLogger("dataloop.service")


class HttpMethod:
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PATCH = "PATCH"


@attr.s
class Webhook(entities.BaseEntity):
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
    def from_json(cls, _json: dict, client_api: services.ApiClient, project=None):
        if project is not None:
            if project.id != _json.get('project', None):
                logger.warning('Webhook has been fetched from a project that is not in it projects list')
                project = None
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
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def webhooks(self):
        if self._webhooks is None:
            self._webhooks = repositories.Webhooks(client_api=self._client_api, project=self._project)
        assert isinstance(self._webhooks, repositories.Webhooks)
        return self._webhooks

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
