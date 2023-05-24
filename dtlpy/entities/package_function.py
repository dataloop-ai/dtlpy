import logging
import typing
import json
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


class PackageFunction(entities.DlEntity):
    """
    Webhook object
    """

    # platform
    name: str = entities.DlProperty(location=['name'],
                                    _type=str,
                                    default=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME)
    description: str = entities.DlProperty(location=['description'],
                                           _type=str)
    display_name: typing.Union[str, None] = entities.DlProperty(location=['displayName'],
                                                                _type=typing.Union[str, None])
    display_icon: typing.Union[str, None] = entities.DlProperty(location=['displayIcon'],
                                                                _type=typing.Union[str, None])

    outputs: typing.Union[typing.List['entities.FunctionIO'], None] = entities.DlProperty(location=['output'],
                                                                                          _kls='FunctionIO')
    inputs: typing.Union[typing.List['entities.FunctionIO'], None] = entities.DlProperty(location=['input'],
                                                                                         _kls='FunctionIO')

    def __repr__(self):
        # TODO need to move to DlEntity
        return f"PackageFunction(name={self.name}, description={self.description})"

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json.copy())
        return inst

    @outputs.default
    def get_outputs(self):
        outputs = list()
        return outputs

    @inputs.default
    def get_inputs(self):
        inputs = list()
        return inputs

    def to_json(self):
        _json = self._dict.copy()
        return _json


class FunctionIO(entities.DlEntity):
    INPUT_TYPES: list = [val for key, val in PackageInputType.__dict__.items() if not key.startswith('_')]
    type = entities.DlProperty(location=['type'], _type=str)
    value = entities.DlProperty(location=['value'], _type=str)
    name = entities.DlProperty(location=['name'], _type=str)
    actions = entities.DlProperty(location=['actions'], _type=list)

    def __repr__(self):
        # TODO need to move to DlEntity
        return f"FunctionIO(type={self.type}, name={self.name}, value={self.value})"

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

    @type.validator
    def check_type(self, value):
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

    @value.validator
    def check_value(self, value):
        value_ok = True
        expected_value = 'Expected value should be:'
        if self.type == PackageInputType.JSON:
            expected_value = '{} json serializable'.format(expected_value)
            if not self.is_json_serializable(value):
                value_ok = False
        else:
            expected_value = 'Unknown value type: {}'.format(type(value))
            if type(value) not in [dict, str, float, int, bool, list]:
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
                'type': self.type,
            }
            if self.actions:
                _json['actions'] = self.actions
        elif resource in ['execution', 'service']:
            _json = {
                self.name: self.value
            }
        else:
            raise exceptions.PlatformException('400', 'Please select resource from: package, execution')

        return _json

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json.copy())
        return inst
