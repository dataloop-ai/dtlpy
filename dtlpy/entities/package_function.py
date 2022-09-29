import logging
import json

import attr

from enum import Enum
from .. import exceptions, entities

logger = logging.getLogger(name='dtlpy')


class PackageInputType(str, Enum):
    DATASET = "Dataset"
    ITEM = "Item"
    ANNOTATION = "Annotation"
    EXECUTION = "Execution"
    TASK = "Task"
    ASSIGNMENT = "Assignment"
    SERVICE = "Service"
    PACKAGE = "Package"
    PROJECT = "Project"
    RECIPE = "Recipe"
    JSON = "Json"
    STRING = "String"
    NUMBER = "Number"
    INT = "Integer"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    MODEL = "Model"
    DATASETS = "Dataset[]"
    ITEMS = "Item[]"
    ANNOTATIONS = "Annotation[]"
    EXECUTIONS = "Execution[]"
    TASKS = "Task[]"
    ASSIGNMENTS = "Assignment[]"
    SERVICES = "Service[]"
    PACKAGES = "Package[]"
    PROJECTS = "Project[]"
    JSONS = "Json[]"
    STRINGS = "String[]"
    NUMBERS = "Number[]"
    INTS = "Integer[]"
    FLOATS = "Float[]"
    BOOLEANS = "Boolean[]"
    MODELS = "Model[]"
    RECIPES = "Recipe[]"


@attr.s
class PackageFunction(entities.BaseEntity):
    """
    Webhook object
    """
    # platform
    outputs = attr.ib()
    name = attr.ib()
    description = attr.ib(default='')
    inputs = attr.ib()
    display_name = attr.ib(default=None)
    display_icon = attr.ib(repr=False, default=None)

    @name.default
    def set_name(self):
        logger.warning('No function name was given. Using default name: {}'.format(
            entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME))
        return entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME

    @classmethod
    def from_json(cls, _json):
        inputs = [FunctionIO.from_json(_io) for _io in _json.get('input', list())]
        outputs = [FunctionIO.from_json(_io) for _io in _json.get('output', list())]

        return cls(
            description=_json.get("description", None),
            name=_json.get("name", None),
            inputs=inputs,
            outputs=outputs,
            display_name=_json.get('displayName', None),
            display_icon=_json.get('displayIcon', None)
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
                                        attr.fields(PackageFunction).display_name,
                                        attr.fields(PackageFunction).display_icon,
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
        if self.display_name is not None:
            _json['displayName'] = self.display_name
        _json['displayIcon'] = self.display_icon
        return _json


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
        else:
            return 'config'

    # noinspection PyUnusedLocal
    @type.validator
    def check_type(self, attribute, value):
        if value not in self.INPUT_TYPES:
            raise exceptions.PlatformException(
                error='400',
                message='Invalid input type: {!r}. Please one from dl.PackageInputType'.format(value))

    @staticmethod
    def is_json_serializable(val):
        try:
            json.dumps(val)
            is_json_serializable = True
        except Exception:
            is_json_serializable = False
        return is_json_serializable

    # noinspection PyUnusedLocal
    @value.validator
    def check_value(self, attribute, value):
        value_ok = True
        expected_value = 'Expected value should be:'
        if self.type == PackageInputType.JSON:
            expected_value = '{} json serializable'.format(expected_value)
            if not self.is_json_serializable(value):
                value_ok = False
        else:
            expected_value = 'Unknown value type: {}'.format(type(value))
            if type(value) not in [dict, str, float, int, bool]:
                value_ok = False

        if not value_ok and value is not None:
            raise exceptions.PlatformException('400', 'Illegal value. {}'.format(expected_value))

    def to_json(self, resource='package'):
        """
        :param resource:
        """
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
