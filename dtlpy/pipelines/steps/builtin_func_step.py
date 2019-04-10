import os
import logging

from . import pipeline_step
from ..misc import get_value_from_context


class BuiltinFuncStep(pipeline_step.PipelineStep):
    def __init__(self, step_dict=None):
        super(BuiltinFuncStep, self).__init__()
        self.name = 'BuiltinFunc'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.args = step_dict['args']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'cmd', 'from': 'cmd', 'by': 'ref', 'type':'string'}]
            self.kwargs = {}
            self.args = []
            self.outputs = []

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            if input_arg['by'] == 'ref':
                if input_arg['from'] in pipeline_dict:
                    raise ValueError('input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from'])
        # get input item 'name' from 'from'

        args_list = list()
        for arg in self.args:
            args_list.append(get_value_from_context(params=arg, context=pipeline_dict))

        cmd = get_value_from_context(params=self.inputs, context=pipeline_dict, name='cmd')
        cmd_list = cmd.split('.')
        outputs = None
        if cmd_list[0] == 'os':
            if cmd_list[1] == 'path':
                if cmd_list[2] == 'join':
                    outputs = os.path.join(*args_list, **self.kwargs)
                elif cmd_list[2] == 'relpath':
                    outputs = os.path.relpath(*args_list, **self.kwargs)
                else:
                    raise ValueError('unsupported option: %s' % cmd_list)
            else:
                raise ValueError('unsupported option: %s' % cmd_list)
        elif cmd_list[0] == 'getattr':
            outputs = getattr(*args_list)
        else:
            raise ValueError('unsupported option: %s' % cmd_list)

        #####
        # handle output
        if outputs is not None:
            # Save outputs arguments
            if not isinstance(outputs, tuple):
                # single output - put in tuple
                outputs = (outputs,)
            for i_output, output_arg in enumerate(self.outputs):
                pipeline_dict[output_arg['name']] = outputs[i_output]
        return pipeline_dict





