from collections import namedtuple
from typing import List

import attr
from dataclasses import dataclass

from .. import entities, services, repositories, miscellaneous as misc


@dataclass
class Hook:
    name: str
    html_tag: str
    location: str
    display_name: str
    description: str
    emit: str


@attr.s()
class Panel:
    name = attr.ib(type=str)
    min_role = attr.ib(type=str)
    icon = attr.ib(type=str)

    supported_slots = attr.ib(type=list, default=[])
    metadata = attr.ib(type=dict, default={})
    default_settings = attr.ib(type=dict, default={})

    def to_json(self) -> dict:
        _json = {
            'name': self.name,
            'minRole': self.min_role,
            'icon': self.icon,
            'supportedSlots': self.supported_slots,
            'metadata': self.metadata,
            'defaultSettings': self.default_settings
        }
        return _json

    @classmethod
    def from_json(cls, _json):
        return cls(
            supported_slots=_json.get('supportedSlots', []),
            name=_json.get('name', None),
            min_role=_json.get('minRole', None),
            icon=_json.get('icon', None),
            metadata=_json.get('metadata', {}),
            default_settings=_json.get('defaultSettings', {})
        )


@dataclass
class Components:
    panels: List[Panel]
    modules: List[entities.PackageModule]
    services: List[entities.Service]
    triggers: List[entities.Trigger]
    pipelines: List[entities.Pipeline]
    hooks: List[Hook]
    models: List[entities.Model]


@attr.s()
class Dpk(entities.BaseEntity):
    # name change
    id = attr.ib(type=str)
    name = attr.ib(type=str)
    version = attr.ib(type=dict)
    categories = attr.ib(type=List[str])
    created_at = attr.ib(type=str)
    updated_at = attr.ib(type=str)
    creator = attr.ib(type=str)
    display_name = attr.ib(type=str)
    icon = attr.ib(type=str)
    tags = attr.ib(type=List[str])
    codebase = attr.ib(type=entities.Codebase)
    scope = attr.ib(type=str)

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _project = attr.ib(repr=False)
    _repositories = attr.ib(repr=False)

    # defaults
    components = attr.ib(type=dict, default={})
    description = attr.ib(type=str, default='')
    url = attr.ib(type=str, default='')

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['dpks', 'codebases', 'organizations'])

        r = reps(dpks=repositories.Dpks(client_api=self._client_api, project=self.project),
                 codebases=repositories.Codebases(client_api=self._client_api),
                 organizations=repositories.Organizations(client_api=self._client_api)
                 )
        return r

    @property
    def codebases(self):
        assert isinstance(self._repositories.codebases, repositories.Codebases)
        return self._repositories.codebases

    @property
    def organizations(self):
        assert isinstance(self._repositories.organizations, repositories.Organizations)
        return self._repositories.organizations

    @property
    def project(self):
        return self._project

    @property
    def dpks(self) -> 'repositories.Dpks':
        assert isinstance(self._repositories.dpks, repositories.Dpks)
        return self._repositories.dpks

    def publish(self):
        """
        Publish the dpk to Dataloop platform.

        **Example**
        .. code-block:: python
            published_dpk = dpk.publish()
        """
        return self.dpks.publish(dpk=self)

    def pull(self, local_path):
        """
        Pulls the app from the platform as dpk file.

        Note: you must pass either dpk_name or dpk_id to the function.
        :param local_path: the path where you want to install the dpk file.
        :return local path where the package pull

        **Example**
        ..code-block:: python
            path = dl.dpks.pull(dpk_name='my-app')
        """
        return self.dpks.pull(dpk_id=self.id, dpk_name=self.name, local_path=local_path)

    def delete(self):
        """
        Delete the dpk from the app store.

        Note: after removing the dpk, you cant get it again, it's advised to pull it first.

        :return whether the operation ran successfully
        :rtype bool
        """
        return self.dpks.delete(self.id)

    def revisions(self):
        """
        returns the available versions of the dpk.

        :return the available versions of the dpk.

        ** Example **
        ..code-block:: python
            versions = dl.dpks.revisions(dpk_id='id')
        """
        return self.dpks.revisions(self.id)

    # noinspection PyProtectedMember
    def to_json(self):
        """
        convert the class to json
        """
        # noinspection PyDictCreation
        _json = {}
        _json['id'] = misc.JsonUtils.get_if_absent(self.id, '')
        _json['name'] = misc.JsonUtils.get_if_absent(self.name, '')
        _json['version'] = misc.JsonUtils.get_if_absent(self.version, '')
        _json['categories'] = misc.JsonUtils.get_if_absent(self.categories, [])
        _json['createdAt'] = misc.JsonUtils.get_if_absent(self.created_at, '')
        _json['updatedAt'] = misc.JsonUtils.get_if_absent(self.updated_at, '')
        _json['creator'] = misc.JsonUtils.get_if_absent(self.creator, '')
        _json['displayName'] = misc.JsonUtils.get_if_absent(self.display_name, _json['name'])
        _json['icon'] = misc.JsonUtils.get_if_absent(self.icon, '')
        _json['tags'] = misc.JsonUtils.get_if_absent(self.tags, [])
        if self.codebase is not None:
            _json['codebase'] = self.codebase.to_json()
        else:
            _json['codebase'] = {}

        _json['scope'] = misc.JsonUtils.get_if_absent(self.scope, '')
        _json['components'] = misc.JsonUtils.get_if_absent(self.components_to_json(self.components), {})
        _json['description'] = misc.JsonUtils.get_if_absent(self.description, '')
        _json['url'] = misc.JsonUtils.get_if_absent(self.url, '')

        return _json

    @classmethod
    def from_json(cls, _json, client_api: services.ApiClient, project: entities.Project,
                  is_fetched=True) -> 'Dpk':
        """
        Turn platform representation of app into an app entity

        :param dict _json: platform representation of package
        :param dl.ApiClient client_api: ApiClient entity
        :param dl.entities.Project project: The project where the dpk resides
        :param bool is_fetched: is Entity fetched from Platform
        :return: App entity
        :rtype: dtlpy.entities.App
        """

        components = cls.__components_from_json(_json.get('components', {}), client_api, project)
        codebase = _json.get('codebase', None)
        if codebase is not None:
            codebase = entities.Codebase.from_json(codebase, client_api)

        instance = cls(
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            name=_json.get('name', None),
            display_name=_json.get('displayName', None),
            scope=_json.get('scope', None),
            client_api=client_api,
            description=_json.get('description', None),
            icon=_json.get('icon', None),
            categories=_json.get('categories', []),
            components=components,
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updateAt', None),
            id=_json.get('id', None),
            codebase=codebase,
            url=_json.get('url', None),
            tags=_json.get('tags', []),
            project=project
        )
        instance.is_fetched = is_fetched
        return instance

    @classmethod
    def __components_from_json(cls, _json, client_api: services.ApiClient, project: entities.Project) -> dict:
        modules = [entities.PackageModule.from_json(module) for module in _json.get('modules', [])]
        _services = [entities.Service.from_json(service, client_api) for service in _json.get('services', [])]
        triggers = [entities.Trigger.from_json(trigger, client_api, project=project) for trigger in
                    _json.get('triggers', [])]
        pipelines = [entities.Pipeline.from_json(pipeline, client_api, project=project) for pipeline in
                     _json.get('pipelines', [])]
        models = [entities.Model.from_json(model, client_api, project=project) for model in _json.get('models', [])]
        return {
            'panels': [Panel.from_json(panel) for panel in _json.get('panels', [])],
            'modules': modules,
            'services': _services,
            'triggers': triggers,
            'pipelines': pipelines,
            'models': models,
            'hooks': _json.get('hooks', [])
        }

    @classmethod
    def components_to_json(cls, components):
        modules = [module.to_json() for module in components['modules']]
        _services = [service.to_json() for service in components['services']]
        triggers = [trigger.to_json() for trigger in components['triggers']]
        pipelines = [pipeline.to_json() for pipeline in components['pipelines']]
        models = [model.to_json() for model in components['models']]
        return {
            'panels': [panel.to_json() for panel in components.get('panels', [])],
            'modules': modules,
            'services': _services,
            'triggers': triggers,
            'pipelines': pipelines,
            'models': models
        }
