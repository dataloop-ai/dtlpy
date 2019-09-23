from collections import namedtuple
import logging
import attr

from .. import utilities, repositories, services, entities

logger = logging.getLogger(name=__name__)


@attr.s
class Plugin:
    """
    Plugin object
    """
    # platform
    id = attr.ib()
    url = attr.ib()
    version = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    name = attr.ib()
    packageId = attr.ib()
    inputs = attr.ib()
    outputs = attr.ib()
    revisions = attr.ib()

    # name change
    project_id = attr.ib()

    # sdk
    _project = attr.ib()
    _client_api = attr.ib(type=services.ApiClient)
    _repositories = attr.ib()

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['sessions', 'deployments', 'projects'])
        r = reps(sessions=repositories.Sessions(client_api=self._client_api),
                 deployments=repositories.Deployments(client_api=self._client_api, plugin=self),
                 projects=repositories.Projects(client_api=self._client_api))
        return r

    @property
    def sessions(self):
        assert isinstance(self._repositories.sessions, repositories.Sessions)
        return self._repositories.sessions

    @property
    def deployments(self):
        assert isinstance(self._repositories.deployments, repositories.Deployments)
        return self._repositories.deployments

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def project(self):
        if self._project is None and self.project_id is not None:
            self._project = self.projects.get(project_id=self.project_id)
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def git_status(self):
        status = 'Git status unavailable'
        try:
            package = self.project.packages.get(package_id=self.packageId, version=self.version-1)
            if 'git' in package.metadata:
                status = package.metadata['git'].get('status', status)
        except Exception:
            logging.debug('Error getting package')
        return status

    @property
    def git_log(self):
        log = 'Git log unavailable'
        try:
            package = self.project.packages.get(package_id=self.packageId, version=self.version-1)
            if 'git' in package.metadata:
                log = package.metadata['git'].get('log', log)
        except Exception:
            logging.debug('Error getting package')
        return log

    @classmethod
    def from_json(cls, _json, client_api, project):
        """
        Turn platform representation of plugin into a Plugin entity

        :param _json: platform representation of plugin
        :param client_api:
        :param project:
        :return: Plugin entity
        """
        return cls(
            project_id=_json.get('project', None),
            packageId=_json.get('packageId', None),
            outputs=_json.get('outputs', list()),
            inputs=_json.get('inputs', list()),
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            revisions=_json['revisions'],
            version=_json['version'],
            client_api=client_api,
            name=_json['name'],
            url=_json['url'],
            project=project,
            id=_json['id']
        )

    def print(self):
        """
        Prints Plugin entity

        :return:
        """
        utilities.List([self]).print()

    def to_json(self):
        """
        Turn Plugin entity into a platform representation of plugin

        :return: platform json of plugin
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Plugin)._project,
                                                        attr.fields(Plugin)._client_api,
                                                        attr.fields(Plugin).project_id,
                                                        attr.fields(Plugin)._repositories))
        _json['project'] = self.project_id
        return _json

    def update(self):
        """
        Update Plugin changes to platform

        :return: Plugin entity
        """
        return self.project.plugins.update(plugin=self)

    def status(self):
        """
        Get plugin status

        :return:
        """
        return self.project.plugins.status(plugin_name=self.name, plugin_id=self.id)

    def stop(self):
        """
        Stop plugin

        :return: True
        """
        return self.project.plugins.stop(plugin_id=self.id, plugin_name=self.name)

    def deploy(self, deployment_name=None):
        """
        Deploy plugin

        :param deployment_name:
        :param revision:
        :return:
        """
        return self.project.plugins.deploy(plugin=self,
                                           deployment_name=deployment_name)

    def checkout(self):
        """
        Checkout as plugin

        :return:
        """
        return self.project.plugins.checkout(plugin_name=self.name)

    def delete(self):
        """
        Delete Plugin object

        :return: True
        """
        return self.project.plugins.delete(plugin=self)

    def push(self, package_id=None, src_path=None, inputs=None, outputs=None):
        """
        Push local plugin

        :param package_id:
        :param src_path:
        :param inputs:
        :param outputs:
        :return:
        """
        return self.project.plugins.push(plugin_name=self.name,
                                         package_id=package_id,
                                         src_path=src_path,
                                         inputs=inputs,
                                         outputs=outputs)


@attr.s
class PluginInput:
    path = attr.ib()
    resource = attr.ib()
    by = attr.ib()
    constValue = attr.ib()

    def to_json(self):
        return attr.asdict(self)

    @classmethod
    def from_json(cls, _json):
        return cls(
            path=_json.get('path', None),
            resource=_json.get('resource', None),
            by=_json.get('by', None),
            constValue=_json.get('constValue', None)
        )


@attr.s
class PluginOutput:
    name = attr.ib()
    type = attr.ib()
    value = attr.ib()

    def to_json(self):
        return attr.asdict(self)

    @classmethod
    def from_json(cls, _json):
        return cls(
            name=_json.get('name', None),
            type=_json.get('type', None),
            value=_json.get('value', None)
        )
