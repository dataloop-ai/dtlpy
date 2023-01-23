import importlib.util
import inspect
import logging
import typing

from .. import entities

logger = logging.getLogger(name='dtlpy')


class PackageModule(entities.DlEntity):
    """
    PackageModule object
    """
    # platform
    name: str = entities.DlProperty(location=['name'], _type=str)
    init_inputs: typing.List['entities.FunctionIO'] = entities.DlProperty(location=['initInputs'],
                                                                          _type=typing.Union[list, None],
                                                                          _kls='FunctionIO')

    entry_point = entities.DlProperty(location=['entryPoint'],
                                      _type=str,
                                      default=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT)
    class_name = entities.DlProperty(location=['className'],
                                     _type=dict,
                                     default=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME)
    functions: typing.List['entities.PackageFunction'] = entities.DlProperty(location=['functions'],
                                                                             _type=list,
                                                                             default=list(),
                                                                             _kls='PackageFunction')

    def __repr__(self):
        # TODO need to move to DlEntity
        return f"PackageModule(name={self.name}, entry_point={self.entry_point}, class_name={self.class_name})"

    @functions.validator
    def validate_functions(self, value: list):
        if not isinstance(value, list):
            raise Exception('Module functions must be a list.')
        if not self.unique_functions(value):
            raise Exception('Cannot have 2 functions by the same name in one module.')

    @staticmethod
    def unique_functions(functions: list):
        return len(functions) == len(set([function.name for function in functions]))

    @name.default
    def set_name(self):
        logger.warning('No module name was given. Using default name: {}'.format(
            entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME))
        return entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME

    @init_inputs.default
    def set_init_inputs(self):
        return list()

    @classmethod
    def from_json(cls, _json):
        inst = cls(_dict=_json)
        return inst

    @classmethod
    def from_entry_point(cls, entry_point):
        """
        Create a dl.PackageModule entity using decorator on the service class.

        :param entry_point: path to the python file with the runner class (relative to the package path)
        :return:
        """
        file_spec = importlib.util.spec_from_file_location(entry_point, entry_point)
        file_module = importlib.util.module_from_spec(file_spec)
        file_spec.loader.exec_module(file_module)
        module = None
        for cls_name, cls_inst in inspect.getmembers(file_module, predicate=inspect.isclass):
            spec = getattr(cls_inst, '__dtlpy__', None)
            if spec is not None:
                spec['entryPoint'] = entry_point
                module = cls.from_json(spec)
                break
        if module is None:
            raise ValueError('Failed to find a decorated Runner class in file: {}'.format(entry_point))
        return module

    def add_function(self, function):
        """
        :param function:
        """
        if not isinstance(self.functions, list):
            self.functions = [self.functions]
        if isinstance(function, entities.PackageFunction):
            self.functions.append(function)
        elif isinstance(function, dict):
            self.functions.append(entities.PackageFunction.from_json(function))
        else:
            raise ValueError('Unknown function type: {}. Expecting dl.PackageFunction or dict')

    def to_json(self):
        _json = self._dict.copy()
        return _json
