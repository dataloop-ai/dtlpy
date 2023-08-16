import logging

import attr
import typing
from enum import Enum
from .. import entities

logger = logging.getLogger(name='dtlpy')


class SlotPostActionType(str, Enum):
    DOWNLOAD = 'download'
    DRAW_ANNOTATION = 'drawAnnotation'
    NO_ACTION = 'noAction'


class SlotDisplayScopeResource(str, Enum):
    ANNOTATION = 'annotation'
    ITEM = 'item'
    DATASET = 'dataset'
    DATASET_QUERY = 'datasetQuery'
    TASK = 'task'


class UiBindingPanel(str, Enum):
    BROWSER = "browser",
    STUDIO = "studio",
    TABLE = "table",
    ALL = "all"


class SlotPostAction(entities.DlEntity):
    type: str = entities.DlProperty(location=['type'],
                                    _type=str,
                                    default=SlotPostActionType.NO_ACTION)

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json)
        return inst

    def to_json(self):
        _json = self._dict.copy()
        return _json


class SlotDisplayScope(entities.DlEntity):
    resource: str = entities.DlProperty(location=['resource'],
                                        _type=str)
    filters: entities.Filters = entities.DlProperty(location=['filter'],
                                                    _type=entities.Filters)
    panel: str = entities.DlProperty(location=['panel'],
                                     _type=str,
                                     default=UiBindingPanel.ALL)

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json)
        return inst

    @staticmethod
    def get_resource(resource: str):
        if resource in [SlotDisplayScopeResource.DATASET, SlotDisplayScopeResource.DATASET_QUERY]:
            return entities.FiltersResource.DATASET
        elif resource == SlotDisplayScopeResource.ITEM:
            return entities.FiltersResource.ITEM
        elif resource == SlotDisplayScopeResource.ANNOTATION:
            return entities.FiltersResource.ANNOTATION

    def to_json(self):
        _json = self._dict.copy()
        if isinstance(self.filters, entities.Filters):
            _json['filter'] = self.filters.prepare(query_only=True)['filter']
        elif isinstance(self.filters, dict):
            _json['filter'] = self.filters
        return _json


class PackageSlot(entities.DlEntity):
    """
    Webhook object
    """
    # platform
    display_name: str = entities.DlProperty(location=['displayName'],
                                            _type=str)
    display_scopes: typing.Union[typing.List['entities.SlotDisplayScope'], None] = entities.DlProperty(
        location=['displayScopes'],
        _kls='SlotDisplayScope')
    module_name: str = entities.DlProperty(location=['moduleName'],
                                           _type=str,
                                           default='default_module')
    function_name: str = entities.DlProperty(location=['functionName'],
                                             _type=str,
                                             default='run')
    display_icon: str = entities.DlProperty(location=['displayIcon'],
                                            _type=str)
    post_action: SlotPostAction = entities.DlProperty(location=['postAction'],
                                                      _type=str,
                                                      _kls='SlotPostAction')
    default_inputs: typing.Union[typing.List['entities.FunctionIO'], None] = entities.DlProperty(
        location=['defaultInputs'],
        _kls='FunctionIO')
    input_options: list = entities.DlProperty(
        location=['inputOptions'],
        _kls='FunctionIO')

    @post_action.default
    def post_action_setter(self):
        return SlotPostAction(type=SlotPostActionType.NO_ACTION)

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json)
        return inst

    def to_json(self):
        _json = self._dict.copy()
        return _json
