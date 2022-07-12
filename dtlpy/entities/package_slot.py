import logging

import attr

from enum import Enum
from .. import entities

logger = logging.getLogger("dataloop.function")


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


@attr.s
class SlotPostAction:
    type = attr.ib(type=str)

    @classmethod
    def from_json(cls, _json):
        return cls(
            type=_json.get('type', SlotPostActionType.NO_ACTION)
        )

    def to_json(self):
        return {'type': self.type}


@attr.s
class SlotDisplayScope:
    resource = attr.ib(type=str)
    filters = attr.ib(type=entities.Filters, default=None)
    panel = attr.ib(default=UiBindingPanel.ALL, type=str)

    @classmethod
    def from_json(cls, _json):
        resource = _json.get('resource')
        panel = _json.get('panel', None)

        filters = None
        if 'filter' in _json:
            if isinstance(_json['filter'], dict) and len(_json['filter']) > 0:
                filters = entities.Filters(resource=SlotDisplayScope.__get_resource(resource=resource),
                                           use_defaults=False,
                                           custom_filter=_json['filter'].get('filter', _json['filter']))
            else:
                filters = _json.get('filter', None)

        return cls(
            resource=resource,
            filters=filters,
            panel=panel
        )

    @staticmethod
    def __get_resource(resource: str):
        if resource in [SlotDisplayScopeResource.DATASET, SlotDisplayScopeResource.DATASET_QUERY]:
            return entities.FiltersResource.DATASET
        elif resource == SlotDisplayScopeResource.ITEM:
            return entities.FiltersResource.ITEM
        elif resource == SlotDisplayScopeResource.ANNOTATION:
            return entities.FiltersResource.ANNOTATION

    def to_json(self):
        _json = {'resource': self.resource,
                 'panel': self.panel}
        if isinstance(self.filters, entities.Filters):
            _json['filter'] = self.filters.prepare(query_only=True)['filter']
        elif isinstance(self.filters, dict):
            _json['filter'] = self.filters
        return _json


@attr.s
class PackageSlot(entities.BaseEntity):
    """
    Webhook object
    """
    # platform
    module_name = attr.ib(default='default_module')
    function_name = attr.ib(default='run')
    display_name = attr.ib(default=None)
    display_scopes = attr.ib(default=None, type=list)
    display_icon = attr.ib(repr=False, default=None)
    post_action = attr.ib(type=SlotPostAction)
    default_inputs = attr.ib(default=None, type=list)
    input_options = attr.ib(default=None, type=list)

    @post_action.default
    def post_action_setter(self):
        return SlotPostAction(type=SlotPostActionType.NO_ACTION)

    @classmethod
    def from_json(cls, _json):
        post_action = SlotPostAction(type=SlotPostActionType.NO_ACTION)
        if 'postAction' in _json and _json['postAction'] is not None:
            post_action = SlotPostAction.from_json(_json.get('postAction'))

        display_scopes = None
        if 'displayScopes' in _json:
            display_scopes = list()
            for display_scope in _json.get('displayScopes'):
                display_scopes.append(
                    SlotDisplayScope.from_json(_json=display_scope)
                )

        return cls(
            module_name=_json.get('moduleName', None),
            function_name=_json.get('functionName', None),
            post_action=post_action,
            display_icon=_json.get('displayIcon', None),
            display_name=_json.get('displayName', None),
            default_inputs=_json.get('defaultInputs', None),
            input_options=_json.get('inputOptions', None),
            display_scopes=display_scopes,
        )

    def to_json(self):
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(attr.fields(PackageSlot).module_name,
                                        attr.fields(PackageSlot).function_name,
                                        attr.fields(PackageSlot).display_icon,
                                        attr.fields(PackageSlot).display_name,
                                        attr.fields(PackageSlot).post_action,
                                        attr.fields(PackageSlot).display_scopes,
                                        attr.fields(PackageSlot).input_options,
                                        attr.fields(PackageSlot).default_inputs,
                                        ),
        )

        if self.module_name is not None:
            _json['moduleName'] = self.module_name

        if self.display_name is not None:
            _json['functionName'] = self.function_name

        if self.display_icon is not None:
            _json['displayIcon'] = self.display_icon

        if self.display_name is not None:
            _json['displayName'] = self.display_name

        if self.display_scopes is not None:
            _json['displayScopes'] = [ds.to_json() for ds in self.display_scopes]

        if self.post_action is not None:
            _json['postAction'] = self.post_action.to_json()

        if self.input_options is not None:
            _json['inputOptions'] = self.input_options

        if self.default_inputs is not None:
            _json['defaultInputs'] = self.default_inputs

        return _json
