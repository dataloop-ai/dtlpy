import importlib.util
import inspect
import logging
import attr

from .. import entities

logger = logging.getLogger(name='dtlpy')


@attr.s
class PackageModule(entities.BaseEntity):
    """
    PackageModule object
    """
    # platform
    name = attr.ib()
    init_inputs = attr.ib()
    entry_point = attr.ib(default=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT)
    class_name = attr.ib(default=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME)
    _functions = attr.ib()

    @_functions.default
    def set_functions(self):
        functions = list()
        return functions

    @_functions.validator
    def validate_functions(self, attribute, value: list):
        if not isinstance(value, list):
            raise Exception('Module functions must be a list.')
        if not self.unique_functions(value):
            raise Exception('Cannot have 2 functions by the same name in one module.')

    @property
    def functions(self):
        return self._functions

    @functions.setter
    def functions(self, functions: list):
        self.validate_functions(attribute=None, value=functions)
        self._functions = functions

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
        init_inputs = list()
        return init_inputs

    @classmethod
    def from_json(cls, _json):
        # convert to function json to objects
        functions = [entities.PackageFunction.from_json(_function) for _function in _json.get('functions', list())]
        # convert to init inputs json objects
        init_inputs = [entities.FunctionIO(type=inp.get('type', None), name=inp.get('name', None))
                       for inp in _json.get("initInputs", list())]
        return cls(
            init_inputs=init_inputs,
            entry_point=_json.get("entryPoint", entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT),
            class_name=_json.get("className", entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME),
            name=_json.get("name", entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME),
            functions=functions,
        )

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
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(attr.fields(PackageModule)._functions,
                                        attr.fields(PackageModule).entry_point,
                                        attr.fields(PackageModule).class_name,
                                        attr.fields(PackageModule).init_inputs))

        # check in inputs is a list
        init_inputs = self.init_inputs
        if not isinstance(init_inputs, list):
            init_inputs = [init_inputs]
        # if is dtlpy entity convert to dict
        if init_inputs and isinstance(init_inputs[0], entities.FunctionIO):
            init_inputs = [_io.to_json() for _io in init_inputs]

        functions = self.functions

        # check in inputs is a list
        if not isinstance(functions, list):
            functions = [functions]

        # if is dtlpy entity convert to dict
        if functions and isinstance(functions[0], entities.PackageFunction):
            functions = [function.to_json() for function in functions]

        _json['entryPoint'] = self.entry_point
        _json['className'] = self.class_name
        _json['initInputs'] = init_inputs
        _json['functions'] = functions
        return _json
