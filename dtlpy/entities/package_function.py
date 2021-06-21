import logging
import json

import attr

from enum import Enum
from .. import exceptions, entities

logger = logging.getLogger("dataloop.function")


class FunctionPostActionType(str, Enum):
    DOWNLOAD = 'download'
    DRAW_ANNOTATION = 'drawAnnotation'
    NO_ACTION = 'noAction'


class FunctionDisplayScopeResource(str, Enum):
    ANNOTATION = 'annotation'
    ITEM = 'item'
    DATASET = 'dataset'
    DATASET_QUERY = 'datasetQuery'


@attr.s
class FunctionPostAction:
    type = attr.ib(type=str)

    @classmethod
    def from_json(cls, _json):
        return cls(
            type=_json.get('type', FunctionPostActionType.NO_ACTION)
        )

    def to_json(self):
        return {'type': self.type}


@attr.s
class FunctionDisplayScope:
    resource = attr.ib(type=str)
    filters = attr.ib(type=entities.Filters, default=None)

    @classmethod
    def from_json(cls, _json):
        resource = _json.get('resource')
        filters = None
        if 'filter' in _json:
            if isinstance(_json['filter'], dict) and len(_json['filter']) > 0:
                filters = entities.Filters(resource=FunctionDisplayScope.__get_resource(resource=resource),
                                           use_defaults=False,
                                           custom_filter=_json['filter'].get('filter', _json['filter']))
            else:
                filters = _json.get('filter', None)

        return cls(
            resource=resource,
            filters=filters,
        )

    @staticmethod
    def __get_resource(resource: str):
        if resource in [FunctionDisplayScopeResource.DATASET, FunctionDisplayScopeResource.DATASET_QUERY]:
            return entities.FiltersResource.DATASET
        elif resource == FunctionDisplayScopeResource.ITEM:
            return entities.FiltersResource.ITEM
        elif resource == FunctionDisplayScopeResource.ANNOTATION:
            return entities.FiltersResource.ANNOTATION

    def to_json(self):
        _json = {'resource': self.resource}
        if isinstance(self.filters, entities.Filters):
            _json['filter'] = self.filters.prepare(query_only=True)['filter']
        elif isinstance(self.filters, dict):
            _json['filter'] = self.filters

        return _json


@attr.s
class PackageFunction(entities.BaseEntity):
    """
    Webhook object
    """
    # platform
    display_name = attr.ib(default=None)
    display_icon = attr.ib(repr=False, default=None)
    display_scopes = attr.ib(default=None, type=list)
    post_action = attr.ib(default=None, type=FunctionPostAction)
    outputs = attr.ib()
    name = attr.ib()
    description = attr.ib(default='')
    inputs = attr.ib()
    default_inputs = attr.ib(default=None, type=list)
    input_options = attr.ib(default=None, type=list)

    @name.default
    def set_name(self):
        logger.warning('No function name was given. Using default name: {}'.format(
            entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME))
        return entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME

    @classmethod
    def from_json(cls, _json):
        inputs = [FunctionIO.from_json(_io) for _io in _json.get('input', list())]
        outputs = [FunctionIO.from_json(_io) for _io in _json.get('output', list())]

        post_action = None
        if 'postAction' in _json:
            post_action = FunctionPostAction.from_json(_json.get('postAction'))

        display_scopes = None
        if 'displayScopes' in _json:
            display_scopes = list()
            for display_scope in _json.get('displayScopes'):
                display_scopes.append(
                    FunctionDisplayScope.from_json(_json=display_scope)
                )

        return cls(
            description=_json.get("description", None),
            name=_json.get("name", None),
            inputs=inputs,
            outputs=outputs,
            post_action=post_action,
            display_icon=_json.get('displayIcon', None),
            display_name=_json.get('displayName', None),
            default_inputs=_json.get('defaultInputs', None),
            input_options=_json.get('inputOptions', None),
            display_scopes=display_scopes,
        )

    @outputs.default
    def get_outputs(self):
        outputs = list()
        return outputs

    @inputs.default
    def get_inputs(self):
        inputs = list()
        return inputs

    def to_json(self):
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(attr.fields(PackageFunction).inputs,
                                        attr.fields(PackageFunction).outputs,
                                        attr.fields(PackageFunction).display_icon,
                                        attr.fields(PackageFunction).display_name,
                                        attr.fields(PackageFunction).post_action,
                                        attr.fields(PackageFunction).display_scopes,
                                        attr.fields(PackageFunction).input_options,
                                        attr.fields(PackageFunction).display_scopes,
                                        attr.fields(PackageFunction).display_name,
                                        attr.fields(PackageFunction).default_inputs,
                                        ),
        )
        inputs = self.inputs
        # check in inputs is a list
        if not isinstance(inputs, list):
            inputs = [inputs]
        # if is dtlpy entity convert to dict
        if inputs and isinstance(inputs[0], entities.FunctionIO):
            inputs = [_io.to_json() for _io in inputs]

        outputs = self.outputs
        # check in inputs is a list
        if not isinstance(outputs, list):
            outputs = [outputs]
        # if is dtlpy entity convert to dict
        if outputs and isinstance(outputs[0], entities.FunctionIO):
            outputs = [_io.to_json() for _io in outputs]

        _json['input'] = inputs
        _json['output'] = outputs

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


class PackageInputType(str, Enum):
    DATASET = "Dataset",
    ITEM = "Item",
    ANNOTATION = "Annotation",
    EXECUTION = "Execution",
    TASK = "Task",
    ASSIGNMENT = "Assignment",
    SERVICE = "Service",
    PACKAGE = "Package",
    PROJECT = "Project",
    JSON = "Json",
    STRING = "String",
    NUMBER = "Number",
    INT = "Integer",
    FLOAT = "Float",
    BOOLEAN = "Boolean",
    DATASETS = "Dataset[]",
    ITEMS = "Item[]",
    ANNOTATIONS = "Annotation[]",
    EXECUTIONS = "Execution[]",
    TASKS = "Task[]",
    ASSIGNMENTS = "Assignment[]",
    SERVICES = "Service[]",
    PACKAGES = "Package[]",
    PROJECTS = "Project[]",
    JSONS = "Json[]",
    STRINGS = "String[]",
    NUMBERS = "Number[]",
    INTS = "Integer[]",
    FLOATS = "Float[]",
    BOOLEANS = "Boolean[]",
    MODEL = 'Model',
    MODELS = 'Model[]',
    SNAPSHOT = 'Snapshot',
    SNAPSHOTS = 'Snapshot[]'


@attr.s
class FunctionIO:
    INPUT_TYPES = [val for key, val in PackageInputType.__dict__.items() if not key.startswith('_')]
    type = attr.ib(type=str)
    value = attr.ib(default=None)
    name = attr.ib(type=str)

    @name.default
    def set_name(self):
        if self.type == PackageInputType.ITEM:
            return 'item'
        elif self.type == PackageInputType.DATASET:
            return 'dataset'
        elif self.type == PackageInputType.ANNOTATION:
            return 'annotation'
        elif self.type == PackageInputType.PROJECT:
            return 'project'
        elif self.type == PackageInputType.PACKAGE:
            return 'package'
        elif self.type == PackageInputType.SERVICE:
            return 'service'
        elif self.type == PackageInputType.EXECUTION:
            return 'execution'
        elif self.type == PackageInputType.MODEL:
            return 'model'
        elif self.type == PackageInputType.SNAPSHOT:
            return 'snapshot'
        else:
            return 'config'

    # noinspection PyUnusedLocal
    @type.validator
    def check_type(self, attribute, value):
        if value not in self.INPUT_TYPES:
            raise exceptions.PlatformException('400',
                                               'Invalid input type please select from: {}'.format(self.INPUT_TYPES))

    @staticmethod
    def is_json_serializable(val):
        try:
            json.dumps(val)
            is_json_serializable = True
        except Exception:
            is_json_serializable = False
        return is_json_serializable

    # @staticmethod
    # def _check_type(value, attribute, io_type):
    #     if io_type in [
    #         PackageInputType.PROJECT,
    #         PackageInputType.DATASET,
    #         PackageInputType.ITEM,
    #         PackageInputType.ANNOTATION,
    #         PackageInputType.PACKAGE,
    #         PackageInputType.SERVICE,
    #         PackageInputType.EXECUTION,
    #         PackageInputType.TASK,
    #         PackageInputType.ASSIGNMENT,
    #         PackageInputType.PACKAGE,
    #     ]:
    #         return isinstance(value, dict) or isinstance(value, str), 'Invalid value for {} IO. ' \
    #                                                                   'Expected string or dictionary'.format(attribute)
    #     elif io_type in [
    #         PackageInputType.PROJECTS,
    #         PackageInputType.DATASETS,
    #         PackageInputType.ITEMS,
    #         PackageInputType.ANNOTATIONS,
    #         PackageInputType.PACKAGES,
    #         PackageInputType.SERVICES,
    #         PackageInputType.EXECUTIONS,
    #         PackageInputType.TASKS,
    #         PackageInputType.ASSIGNMENTS,
    #         PackageInputType.PACKAGES,
    #         PackageInputType.STRINGS,
    #         PackageInputType.INTS,
    #         PackageInputType.BOOLEANS,
    #         PackageInputType.JSONS
    #     ]:
    #         return isinstance(value, list), 'Invalid value for {} IO. ' \
    #                                         'Expected list'.format(attribute)
    #     elif io_type == PackageInputType.NUMBER:
    #         return isinstance(value, (int, float)), 'Invalid value for {} IO. ' \
    #                                  'Expected int or float'.format(attribute)
    #     elif io_type == PackageInputType.INT:
    #         return isinstance(value, int), 'Invalid value for {} IO. ' \
    #                                  'Expected int'.format(attribute)
    #     elif io_type == PackageInputType.FLOAT:
    #         return isinstance(value, float), 'Invalid value for {} IO. ' \
    #                                  'Expected float'.format(attribute)
    #     elif io_type == PackageInputType.STRING:
    #         return isinstance(value, str), 'Invalid value for {} IO. ' \
    #                                  'Expected str'.format(attribute)
    #     elif io_type == PackageInputType.BOOLEAN:
    #         return isinstance(value, bool), 'Invalid value for {} IO. ' \
    #                                  'Expected bool'.format(attribute)
    #
    # # noinspection PyUnusedLocal
    # @value.validator
    # def check_value(self, attribute, value):
    #     value_ok = True
    #     expected_value = 'Expected value should be:'
    #     if self.type == PackageInputType.JSON:
    #         expected_value = '{} json serializable'.format(expected_value)
    #         if not self.is_json_serializable(value):
    #             value_ok = False
    #     else:
    #         value_ok, expected_value = self._check_type(value=value, attribute=attribute, io_type=expected_value)
    #
    #     if not value_ok and value is not None:
    #         raise exceptions.PlatformException('400', 'Illegal value. {}'.format(expected_value))

    def to_json(self, resource='package'):
        if resource == 'package':
            _json = {
                'name': self.name,
                'type': self.type
            }
        elif resource in ['execution', 'service']:
            _json = {
                self.name: self.value
            }
        else:
            raise exceptions.PlatformException('400', 'Please select resource from: package, execution')

        return _json

    @classmethod
    def from_json(cls, _json):
        return cls(
            type=_json.get('type', None),
            value=_json.get('value', None),
            name=_json.get('name', None)
        )
