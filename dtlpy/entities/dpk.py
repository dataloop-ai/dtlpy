from collections import namedtuple
from dataclasses import dataclass
from typing import List
import traceback
import enum

from .. import entities, services, repositories
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
        return cls(_dict=_json.copy())


class Components(entities.DlEntity):
    panels: List[Panel] = entities.DlProperty(location=['panels'],
                                              _kls='Panel')
    modules: List[entities.PackageModule] = entities.DlProperty(location=['modules'],
                                                                _kls='PackageModule')
    services: List[entities.Service] = entities.DlProperty(location=['services'],
                                                           # _kls='Service'
                                                           )
    triggers: List[entities.Trigger] = entities.DlProperty(location=['triggers'],
                                                           # _kls='Trigger'
                                                           )
    pipelines: List[entities.Pipeline] = entities.DlProperty(location=['pipelines'],
                                                             # _kls='Pipeline'
                                                             )
    toolbars: List[Toolbar] = entities.DlProperty(location=['toolbars'],
                                                  _kls='Toolbar')
    models: List[entities.Model] = entities.DlProperty(location=['models'],
                                                       # _kls='Model'
                                                       )

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

    @pipelines.default
    def default_pipelines(self):
        self._dict['pipelines'] = list()
        return self._dict['pipelines']

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json.copy())
        return inst

    def to_json(self):
        return self._dict.copy()


class Dpk(entities.DlEntity):
    # name change
    id: str = entities.DlProperty(location=['id'], _type=str)
    name: str = entities.DlProperty(location=['name'], _type=str)
    version: str = entities.DlProperty(location=['version'], _type=str)
    categories: list = entities.DlProperty(location=['categories'], _type=list)
    created_at: str = entities.DlProperty(location=['createdAt'], _type=str)
    updated_at: str = entities.DlProperty(location=['updatedAt'], _type=str)
    creator: str = entities.DlProperty(location=['creator'], _type=str)
    display_name: str = entities.DlProperty(location=['displayName'], _type=str)
    icon: str = entities.DlProperty(location=['icon'], _type=str)
    tags: list = entities.DlProperty(location=['tags'], _type=list)
    codebase: str = entities.DlProperty(location=['codebase'], _kls="Codebase")
    scope: dict = entities.DlProperty(location=['scope'], _type=dict)

    # defaults
    components: Components = entities.DlProperty(location=['components'], _kls='Components')
    description: str = entities.DlProperty(location=['name'], _type=str)
    url: str = entities.DlProperty(location=['url'], _type=str)

    # sdk
    client_api: ApiClient
    project: entities.Project
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
                              field_names=['dpks', 'codebases', 'organizations'])

            self.__repositories = reps(dpks=repositories.Dpks(client_api=self.client_api, project=self.project),
                                       codebases=repositories.Codebases(client_api=self.client_api),
                                       organizations=repositories.Organizations(client_api=self.client_api)
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

    def revisions(self):
        """
        returns the available versions of the dpk.

        :return the available versions of the dpk.

        ** Example **
        ..code-block:: python
            versions = dl.dpks.revisions(dpk_name='name')
        """
        return self.dpks.revisions(dpk_name=self.name)

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

        inst = cls(_dict=_json,
                   client_api=client_api,
                   project=project,
                   is_fetched=is_fetched)
        return inst
