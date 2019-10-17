from collections import namedtuple
import logging
import attr

from .. import services, repositories, entities

logger = logging.getLogger("dataloop.deployment")


@attr.s
class Deployment:
    """
    Deployment object
    """
    # platform
    id = attr.ib()
    name = attr.ib()
    url = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    config = attr.ib()  # init param
    runtime = attr.ib()  # hw requirements
    pluginId = attr.ib()
    mq = attr.ib()
    pluginRevision = attr.ib()

    # name change
    project_id = attr.ib()

    # SDK
    _plugin = attr.ib()
    _client_api = attr.ib(type=services.ApiClient)
    # repositories
    _project = attr.ib(default=None)
    _repositories = attr.ib()

    @classmethod
    def from_json(cls, _json, client_api, plugin=None, project=None):
        return cls(
            client_api=client_api,
            plugin=plugin,
            pluginId=_json['pluginId'],
            project_id=_json['project'],
            id=_json["id"],
            name=_json["name"],
            url=_json.get("url", None),
            createdAt=_json.get("createdAt", None),
            updatedAt=_json.get("updatedAt", None),
            pluginRevision=_json.get("pluginRevision", None),
            config=_json.get("config", dict()),
            runtime=_json.get("runtime", dict()),
            mq=_json.get('mq', dict()),
            project=project
        )

    @property
    def project(self):
        if self._project is None:
            projects = repositories.Projects(client_api=self._client_api)
            self._project = projects.get(project_id=self.project_id)
        assert isinstance(self._project, entities.Project)
        return self._project

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['sessions', 'deployments', 'triggers'])
        if self._plugin is None:
            deployments = repositories.Deployments(client_api=self._client_api, plugin=self._plugin,
                                                   project=self.project)
        else:
            deployments = self._plugin.deployments

        triggers = repositories.Triggers(client_api=self._client_api, project=self.project)

        r = reps(sessions=repositories.Sessions(client_api=self._client_api, deployment=self),
                 deployments=deployments, triggers=triggers)
        return r

    @property
    def sessions(self):
        assert isinstance(self._repositories.sessions, repositories.Sessions)
        return self._repositories.sessions

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def deployments(self):
        assert isinstance(self._repositories.deployments, repositories.Deployments)
        return self._repositories.deployments

    @property
    def plugin(self):
        if self._plugin is None:
            self._plugin = repositories.Plugins(client_api=self._client_api).get(plugin_id=self.pluginId)
        assert isinstance(self._plugin, entities.Plugin)
        return self._plugin

    def to_json(self):
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Deployment)._plugin,
                attr.fields(Deployment)._client_api,
                attr.fields(Deployment)._repositories,
                attr.fields(Deployment).project_id,
            ),
        )

        _json['project'] = self.project_id

        return _json

    def update(self):
        """
        Update Deployment changes to platform

        :return: Deployment entity
        """
        return self.deployments.update(deployment=self)

    def delete(self):
        """
        Delete Deployment object

        :return: True
        """
        return self.deployments.delete(deployment_id=self.id)

    def log(self, size=None, checkpoint=None, start=None, end=None):
        """
        Get deployment logs

        :param end:
        :param start:
        :param checkpoint:
        :param size:
        :return: Deployment entity
        """
        return self.deployments.log(deployment=self, size=size, checkpoint=checkpoint, start=start, end=end)
