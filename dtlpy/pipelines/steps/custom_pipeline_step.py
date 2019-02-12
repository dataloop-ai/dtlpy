from . import pipeline_step
import importlib


class CustomPipelineStep(pipeline_step.PipelineStep):
    """
    Custom pipeline step creator
    """

    def __init__(self, step_dict):
        super(CustomPipelineStep, self).__init__()

        if 'inputs' in step_dict:
            self.inputs = step_dict['inputs']
        if 'outputs' in step_dict:
            self.outputs = step_dict['outputs']
        if 'name' in step_dict:
            self.name = step_dict['name']
        if 'kwargs' in step_dict:
            self.kwargs = step_dict['kwargs']

        success = True
        if 'module_location' in step_dict:
            self.module_location = step_dict['module_location']
        else:
            success = False
            print('[ERROR] custom step must contain a module_location')
        if 'module_name' in step_dict:
            self.module_name = step_dict['module_name']
        else:
            success = False
            print('[ERROR] custom step must contain a module_name')
        if 'method_name' in step_dict:
            self.method_name = step_dict['method_name']
        else:
            success = False
            print('[ERROR] custom step must contain a method_name')
        if not success:
            raise ValueError()
        self.func = None
        self.type = 'custom'

    def to_dict(self):
        step = {'name': self.name,
                'inputs': self.inputs,
                'outputs': self.outputs,
                'kwargs': self.kwargs,
                'type': self.type,
                'module_location': self.module_location,
                'module_name': self.module_name,
                'method_name': self.method_name}
        return step

    ###################
    # load dynamically #
    ###################
    def load_module_from_path(self, module_name, module_location):
        spec = importlib.util.spec_from_file_location(module_name, module_location)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        mod = getattr(foo, module_name)
        return mod()

    def load(self):
        # load class dynamically
        cls = self.load_module_from_path(self.module_name, self.module_location)
        self.func = self.load_method_from_class(cls=cls, method_name=self.method_name)
