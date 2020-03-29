import logging
import json
import attr

from .. import miscellaneous, exceptions, entities

logger = logging.getLogger("dataloop.function")


@attr.s
class PackageFunction(entities.BaseEntity):
    """
    Webhook object
    """
    # platform
    name = attr.ib(default='run')
    inputs = attr.ib()
    description = attr.ib(default='')
    outputs = attr.ib()

    @classmethod
    def from_json(cls, _json):
        inputs = [FunctionIO.from_json(_io) for _io in _json.get('input', list())]
        outputs = [FunctionIO.from_json(_io) for _io in _json.get('output', list())]
        return cls(
            description=_json.get("description", None),
            name=_json.get("name", None),
            inputs=inputs,
            outputs=outputs,
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
                                        attr.fields(PackageFunction).outputs),
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

        return _json


@attr.s
class FunctionIO:
    INPUT_TYPES = ['Json', 'Dataset', 'Item', 'Annotation']
    type = attr.ib(type=str)
    value = attr.ib(default=None)
    name = attr.ib(type=str)

    @name.default
    def set_name(self):
        if self.type == 'Item':
            return 'item'
        elif self.type == 'Dataset':
            return 'dataset'
        elif self.type == 'Annotation':
            return 'annotation'
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

    # noinspection PyUnusedLocal
    @value.validator
    def check_value(self, attribute, value):
        value_ok = True
        expected_value = 'Expected value should be:'
        if self.type == 'Json':
            expected_value = '{} json serializable'.format(expected_value)
            if not self.is_json_serializable(value):
                value_ok = False
        elif self.type == 'Dataset':
            expected_value = '{} {{"dataset_id": <dataset id>}}'.format(expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'dataset_id' not in value:
                    value_ok = False
        elif self.type == 'Item':
            expected_value = '{} {{"item_id": <item id>}}'.format(expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'item_id' not in value:
                    value_ok = False
        elif self.type == 'Annotation':
            expected_value = '{} {{"item_id": <item id>, "annotation_id": <annotation id>}}'.format(expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'item_id' not in value:
                    value_ok = False
                if 'dataset_id' not in value:
                    value_ok = False
                if 'annotation_id' not in value:
                    value_ok = False

        if not value_ok and value is not None:
            raise exceptions.PlatformException('400', 'Illegal value. {}'.format(expected_value))

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
