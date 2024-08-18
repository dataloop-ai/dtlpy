from collections import namedtuple
from typing import List, Union
import traceback
import enum

from .. import entities, repositories, exceptions
from ..services.api_client import ApiClient


class SlotType(str, enum.Enum):
    ITEM_VIEWER = 'itemViewer'
    FLOATING_WINDOW = 'floatingWindow'


DEFAULT_STOPS = {SlotType.ITEM_VIEWER: {"type": "itemViewer",
                                        "configuration": {"layout": {"leftBar": True,
                                                                     "rightBar": True,
                                                                     "bottomBar": True,
                                                                     }
                                                          }
                                        },
                 SlotType.FLOATING_WINDOW: {"type": "floatingWindow",
                                            "configuration": {"layout": {"width": 455,
                                                                         "height": 340,
                                                                         "resizable": True,
                                                                         "backgroundColor": "dl-color-studio-panel"
                                                                         }
                                                              }
                                            }
                 }


class Slot(entities.DlEntity):
    type = entities.DlProperty(location=['type'], _type=str)
    configuration = entities.DlProperty(location=['configuration'], _type=dict)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Toolbar(entities.DlEntity):
    display_name: str = entities.DlProperty(location=['displayName'], _type=str)
    conditions: dict = entities.DlProperty(location=['conditions'], _type=dict)
    invoke: dict = entities.DlProperty(location=['invoke'], _type=dict)
    location: str = entities.DlProperty(location=['location'], _type=str)
    icon: str = entities.DlProperty(location=['icon'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Panel(entities.DlEntity):
    name = entities.DlProperty(location=['name'], _type=str)
    min_role = entities.DlProperty(location=['minRole'], _type=list)
    supported_slots = entities.DlProperty(location=['supportedSlots'], _type=list)

    metadata = entities.DlProperty(location=['metadata'], _type=list)
    default_settings = entities.DlProperty(location=['defaultSettings'], _type=list)
    conditions = entities.DlProperty(location=['conditions'], _type=list)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class ToolbarInvoke(entities.DlEntity):
    type: str = entities.DlProperty(location=['type'], _type=str)
    panel: str = entities.DlProperty(location=['panel'], _type=str)
    namespace: str = entities.DlProperty(location=['namespace'], _type=str)
    source: str = entities.DlProperty(location=['source'], _type=str)
    input_options: dict = entities.DlProperty(location=['inputOptions'], _type=dict)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class CustomNodeScope(str, enum.Enum):
    GLOBAL = "global",
    PROJECT = "project",
    NODE = 'node'


class PipelineNode(entities.DlEntity):
    display_name: str = entities.DlProperty(location=['displayName'], _type=str)
    panel: str = entities.DlProperty(location=['panel'], _type=str)
    invoke: ToolbarInvoke = entities.DlProperty(location=['invoke'], _kls='ToolbarInvoke')
    icon: str = entities.DlProperty(location=['icon'], _type=str)
    categories: List[str] = entities.DlProperty(location=['categories'], _type=list)
    description: str = entities.DlProperty(location=['description'], _type=str)
    configuration: dict = entities.DlProperty(location=['configuration'], _type=dict)
    scope: CustomNodeScope = entities.DlProperty(location=['scope'], _type=CustomNodeScope)
    compute_config: str = entities.DlProperty(location=['computeConfig'], _type=str, default=None)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class DpkComputeConfig(entities.DlEntity):
    run_execution_as_process: bool = entities.DlProperty(location=['runExecutionAsProcess'], _type=bool)
    execution_timeout: int = entities.DlProperty(location=['executionTimeout'], _type=int)
    drain_time: int = entities.DlProperty(location=['drainTime'], _type=int)
    on_reset: str = entities.DlProperty(location=['onReset'], _type=str)
    runtime: dict = entities.DlProperty(location=['runtime'], _type=dict)
    bot_user_name: str = entities.DlProperty(location=['botUserName'], _type=str)
    max_attempts: int = entities.DlProperty(location=['maxAttempts'], _type=int)
    use_user_jwt: bool = entities.DlProperty(location=['useUserJwt'], _type=bool)
    driver_id: str = entities.DlProperty(location=['driverId'], _type=str)
    versions: dict = entities.DlProperty(location=['versions'], _type=dict)
    name: str = entities.DlProperty(location=['name'], _type=str)
    integrations: List[dict] = entities.DlProperty(location=['integrations'], _type=list)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class DpkComponentChannel(entities.DlEntity):
    name: str = entities.DlProperty(location=['name'], _type=str)
    icon: str = entities.DlProperty(location=['icon'], _type=str)
    description: str = entities.DlProperty(location=['description'], _type=str)
    is_global: bool = entities.DlProperty(location=['global'], _type=bool)
    metadata: dict = entities.DlProperty(location=['metadata'], _type=dict)
    context: dict = entities.DlProperty(location=['context'], _type=dict)
    filters: List[dict] = entities.DlProperty(location=['filters'], _type=list)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Components(entities.DlEntity):
    panels: List[Panel] = entities.DlProperty(location=['panels'], _kls='Panel')
    modules: List[entities.PackageModule] = entities.DlProperty(location=['modules'], _kls='PackageModule')
    services: List[dict] = entities.DlProperty(location=['services'])
    triggers: List[dict] = entities.DlProperty(location=['triggers'])
    pipeline_nodes: List[PipelineNode] = entities.DlProperty(location=['pipelineNodes'])
    toolbars: List[Toolbar] = entities.DlProperty(location=['toolbars'], _kls='Toolbar')
    models: List[dict] = entities.DlProperty(location=['models'])
    compute_configs: List[DpkComputeConfig] = entities.DlProperty(location=['computeConfigs'], _kls='DpkComputeConfig')
    channels: List[DpkComponentChannel] = entities.DlProperty(location=['channels'], _kls='DpkComponentChannel')
    pipeline_templates: List[dict] = entities.DlProperty(location=['pipelineTemplates'])
    integrations: List[dict] = entities.DlProperty(location=['integrations'])

    @panels.default
    def default_panels(self):
        self._dict['panels'] = list()
        return self._dict['panels']

    @modules.default
    def default_modules(self):
        self._dict['modules'] = list()
        return self._dict['modules']

    @services.default
    def default_services(self):
        self._dict['services'] = list()
        return self._dict['services']

    @triggers.default
    def default_triggers(self):
        self._dict['triggers'] = list()
        return self._dict['triggers']

    @pipeline_nodes.default
    def default_pipelines(self):
        self._dict['pipelines'] = list()
        return self._dict['pipelines']

    @toolbars.default
    def default_toolbars(self):
        self._dict['toolbars'] = list()
        return self._dict['toolbars']

    @models.default
    def default_models(self):
        self._dict['models'] = list()
        return self._dict['models']

    @compute_configs.default
    def default_compute_configs(self):
        self._dict['computeConfigs'] = list()
        return self._dict['computeConfigs']

    @channels.default
    def default_channels(self):
        self._dict['channels'] = list()
        return self._dict['channels']

    @pipeline_templates.default
    def default_pipeline_templates(self):
        self._dict['pipelineTemplates'] = list()
        return self._dict['pipelineTemplates']

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json)
        return inst

    def to_json(self):
        return self._dict.copy()


class Dpk(entities.DlEntity):
    # name change
    id: str = entities.DlProperty(location=['id'], _type=str)
    base_id: str = entities.DlProperty(location=['baseId'], _type=str)
    name: str = entities.DlProperty(location=['name'], _type=str)
    version: str = entities.DlProperty(location=['version'], _type=str)
    attributes: list = entities.DlProperty(location=['attributes'], _type=dict)
    created_at: str = entities.DlProperty(location=['createdAt'], _type=str)
    updated_at: str = entities.DlProperty(location=['updatedAt'], _type=str)
    creator: str = entities.DlProperty(location=['creator'], _type=str)
    display_name: str = entities.DlProperty(location=['displayName'], _type=str)
    icon: str = entities.DlProperty(location=['icon'], _type=str)
    tags: list = entities.DlProperty(location=['tags'], _type=list)
    codebase: str = entities.DlProperty(location=['codebase'], _kls="Codebase")
    scope: dict = entities.DlProperty(location=['scope'], _type=str)
    context: dict = entities.DlProperty(location=['context'], _type=dict)
    metadata: dict = entities.DlProperty(location=['metadata'], _type=dict)
    dependencies: dict = entities.DlProperty(location=['dependencies'], _type=List[dict])

    # defaults
    components: Components = entities.DlProperty(location=['components'], _kls='Components')
    description: str = entities.DlProperty(location=['description'], _type=str)
    url: str = entities.DlProperty(location=['url'], _type=str)

    # sdk
    client_api: ApiClient
    project: entities.Project
    _revisions = None
    __repositories = None

    @components.default
    def default_components(self):
        self._dict['components'] = dict()
        return self._dict['components']

    ################
    # repositories #
    ################
    @property
    def _repositories(self):
        if self.__repositories is None:
            reps = namedtuple('repositories',
                              field_names=['dpks', 'codebases', 'organizations', 'services'])

            self.__repositories = reps(
                dpks=repositories.Dpks(client_api=self.client_api, project=self.project),
                codebases=repositories.Codebases(client_api=self.client_api),
                organizations=repositories.Organizations(client_api=self.client_api),
                services=repositories.Services(client_api=self.client_api, project=self.project, package=self),
            )

        return self.__repositories

    @property
    def codebases(self):
        assert isinstance(self._repositories.codebases, repositories.Codebases)
        return self._repositories.codebases

    @property
    def organizations(self):
        assert isinstance(self._repositories.organizations, repositories.Organizations)
        return self._repositories.organizationsFapp

    @property
    def dpks(self) -> 'repositories.Dpks':
        assert isinstance(self._repositories.dpks, repositories.Dpks)
        return self._repositories.dpks

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    ###########
    # methods #
    ###########
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
        return self.dpks.pull(dpk=self, local_path=local_path)

    def delete(self):
        """
        Delete the dpk from the app store.

        Note: after removing the dpk, you cant get it again, it's advised to pull it first.

        :return whether the operation ran successfully
        :rtype bool
        """
        return self.dpks.delete(self.id)

    def _get_revision_pages(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        returns the available versions of the dpk.

        :param entities.Filters filters: the filters to apply to the search.
        :return the available versions of the dpk.

        ** Example **
        ..code-block:: python
            versions = dl.dpks.revisions(dpk_name='name')
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.DPK)
        elif not isinstance(filters, entities.Filters):
            raise ValueError('Unknown filters type: {!r}'.format(type(filters)))
        elif filters.resource != entities.FiltersResource.DPK:
            raise TypeError('Filters resource must to be FiltersResource.DPK. Got: {!r}'.format(filters.resource))

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self.client_api,
                                       list_function=self._list_revisions)
        paged.get_page()
        return paged

    def _build_entities_from_response(self, response_items):
        return self.dpks._build_entities_from_response(response_items=response_items)

    def _list_revisions(self, filters: entities.Filters):
        url = '/app-registry/{}/revisions'.format(self.name)
        # request
        success, response = self.client_api.gen_request(req_type='post',
                                                        path=url,
                                                        json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @property
    def revisions(self):
        """
        Returns the available versions of the dpk.

        :return List[Dpk]

        ** Example **
        ..code-block:: python
        versions = dpk.revisions
        """
        if self._revisions is None:
            self._revisions = self._get_revision_pages()
        return self._revisions

    def get_revisions(self, version: str):
        """
        Get the dpk with the specified version.

        :param str version: the version of the dpk to get.
        :return: Dpk

        ** Example **
        ..code-block:: python
        dpk = dpk.get_revisions(version='1.0.0')
        """
        return self.dpks.get_revisions(dpk_id=self.base_id, version=version)

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json:  platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            package = Dpk.from_json(_json=_json,
                                    client_api=client_api,
                                    project=project,
                                    is_fetched=is_fetched)
            status = True
        except Exception:
            package = traceback.format_exc()
            status = False
        return status, package

    def to_json(self):
        """
        convert the class to json
        """
        _json = self._dict.copy()
        return _json

    @classmethod
    def from_json(cls,
                  _json,
                  client_api: ApiClient = None,
                  project: entities.Project = None,
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
        res = cls(
            _dict=_json,
            client_api=client_api,
            project=project,
            is_fetched=is_fetched
        )

        return res
