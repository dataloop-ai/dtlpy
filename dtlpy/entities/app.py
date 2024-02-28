from collections import namedtuple
import traceback
import logging
from enum import Enum

import attr

from .. import entities, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class AppScope(str, Enum):
    """ The scope of the app.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - SYSTEM
         - Dataloop internal app
       * - PROJECT
         - Project app
    """
    SYSTEM = 'system'
    PROJECT = 'project'


@attr.s
class App(entities.BaseEntity):
    id = attr.ib(type=str)
    name = attr.ib(type=str)
    url = attr.ib(type=str)
    created_at = attr.ib(type=str)
    updated_at = attr.ib(type=str)
    creator = attr.ib(type=str)
    project_id = attr.ib(type=str)
    org_id = attr.ib(type=str)
    dpk_name = attr.ib(type=str)
    dpk_version = attr.ib(type=str)
    composition_id = attr.ib(type=str)
    scope = attr.ib(type=str)
    routes = attr.ib(type=dict)
    custom_installation = attr.ib(type=dict)
    metadata = attr.ib(type=dict)

    # sdk
    _project = attr.ib(type=entities.Project, repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories', field_names=['projects', 'apps'])
        return reps(
            projects=repositories.Projects(client_api=self._client_api),
            apps=repositories.Apps(client_api=self._client_api, project=self._project)
        )

    @property
    def project(self):
        if self._project is None:
            self._project = self.projects.get(project_id=self.project_id)
        return self._project

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def apps(self):
        assert isinstance(self._repositories.apps, repositories.Apps)
        return self._repositories.apps

    def uninstall(self):
        """
        Uninstall an app installed app from the project.

        **Example**
        .. code-block:: python
            succeed = app.uninstall()
        """
        return self.apps.uninstall(self.id)

    def update(self):
        """
        Update the current app to the new configuration

        :return bool whether the operation ran successfully or not

        **Example**
        .. code-block:: python
            succeed = app.update()
        """
        return self.apps.update(self)

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json:  platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            package = App.from_json(_json=_json,
                                    client_api=client_api,
                                    project=project,
                                    is_fetched=is_fetched)
            status = True
        except Exception:
            package = traceback.format_exc()
            status = False
        return status, package

    def to_json(self):
        _json = {}
        if self.id is not None:
            _json['id'] = self.id
        if self.name is not None:
            _json['name'] = self.name
        if self.url is not None:
            _json['url'] = self.url
        if self.created_at is not None:
            _json['createdAt'] = self.created_at
        if self.updated_at is not None:
            _json['updatedAt'] = self.updated_at
        if self.creator is not None:
            _json['creator'] = self.creator
        if self.project_id is not None:
            _json['projectId'] = self.project_id
        if self.org_id is not None:
            _json['orgId'] = self.org_id
        if self.dpk_name is not None:
            _json['dpkName'] = self.dpk_name
        if self.dpk_version is not None:
            _json['dpkVersion'] = self.dpk_version
        if self.composition_id is not None:
            _json['compositionId'] = self.composition_id
        if self.scope is not None:
            _json['scope'] = self.scope
        if self.routes != {}:
            _json['routes'] = self.routes
        if self.custom_installation != {}:
            _json['customInstallation'] = self.custom_installation
        if self.metadata is not None:
            _json['metadata'] = self.metadata

        return _json

    @classmethod
    def from_json(cls, _json, client_api: ApiClient, project: entities.Project, is_fetched=True):
        app = cls(
            id=_json.get('id', None),
            name=_json.get('name', None),
            url=_json.get('url', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updateAt', None),
            creator=_json.get('creator', None),
            project_id=_json.get('projectId', None),
            org_id=_json.get('orgId', None),
            dpk_name=_json.get('dpkName', None),
            dpk_version=_json.get('dpkVersion', None),
            composition_id=_json.get('compositionId', None),
            scope=_json.get('scope', None),
            routes=_json.get('routes', {}),
            custom_installation=_json.get('customInstallation', {}),
            client_api=client_api,
            project=project,
            metadata=_json.get('metadata', None)
        )
        app.is_fetched = is_fetched
        return app
