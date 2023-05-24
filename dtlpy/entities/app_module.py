import logging
import typing
from enum import Enum

from .. import entities, utilities

logger = logging.getLogger(name='dtlpy')


class AppModule(entities.PackageModule, utilities.BaseServiceRunner):
    def __init__(self, name, description):
        super(AppModule, self).__init__()
        self.name = name
        self.description = description

    def init(self):
        """
        Default init function
        :return:
        """
        ...

    ###############
    # Decorators #
    ###############
    def set_init(self, inputs=None):
        def decorator(func: typing.Callable):
            setattr(self, 'init', func)
            setattr(self, func.__name__, func)
            init_inputs, _ = self._function_io_from_def(func=func, inputs=inputs, outputs=None)
            self.init_inputs = AppModule._parse_io(io_list=init_inputs)
            return func

        return decorator

    def add_function(self, display_name=None, inputs=None, outputs=None):
        """
        Add a function to the instance to be able to run in the FaaS.

        :param display_name: Display name of the function
        :param inputs: function inputs variable definitions. dictionary with strings for name and type {name: type}
        :param outputs: function output variable definitions. dictionary with strings for name and type {name: type}
        :return:
        """

        def decorator(func: typing.Callable):
            if display_name is None:
                d_name = func.__name__
            else:
                d_name = display_name
            module_inputs, module_outputs = self._function_io_from_def(func=func, inputs=inputs, outputs=outputs)
            defs = {"name": func.__name__,
                    "displayName": d_name,
                    "input": AppModule._parse_io(io_list=module_inputs),
                    "output": AppModule._parse_io(io_list=module_outputs)}
            func.__dtlpy__ = defs
            setattr(self, func.__name__, func)
            self.functions.append(entities.PackageFunction.from_json(defs))
            return func

        return decorator

    #########
    # Utils #
    #########
    @staticmethod
    def _function_io_from_def(func, inputs, outputs):
        input_types = typing.get_type_hints(func)
        hint_outputs = input_types.pop('return', None)

        if outputs is None:
            if hint_outputs is not None:
                func_outputs = {'output': hint_outputs}
            else:
                func_outputs = dict()
        else:
            func_outputs = outputs
        if inputs is None:
            func_inputs = {name: t for name, t in input_types.items()}
        else:
            func_inputs = inputs
        return func_inputs, func_outputs

    @staticmethod
    def _function_type_mapping(io_type):
        mapping = {'str': entities.PackageInputType.STRING}
        if io_type in mapping:
            return mapping[io_type]
        else:
            return io_type

    @staticmethod
    def _parse_io(io_list: dict):
        output = list()
        if io_list is not None:
            for io_name, io_type in io_list.items():
                if isinstance(io_type, Enum):
                    io_type = io_type.name
                if hasattr(io_type, '__args__'):
                    io_type = io_type.__args__[0]
                if isinstance(io_type, type):
                    io_type = io_type.__name__
                else:
                    io_type = str(io_type)
                output.append({"name": io_name,
                               "type": AppModule._function_type_mapping(str(io_type))})
        return output
