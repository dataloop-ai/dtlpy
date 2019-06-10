import logging
from . import pipeline_step

# callback and mapping
from ...callbacks.piper_progress_reporter import main as piper_progress_reporter
from ...callbacks.progress_viewer import main as progress_viewer

mapping = {'progress_viewer': progress_viewer,
           'piper_progress_reporter': piper_progress_reporter}


class CallbacksGetStep(pipeline_step.PipelineStep):
    """
    Item upload step creator
    """

    def __init__(self, step_dict=None):
        super(CallbacksGetStep, self).__init__()
        self.name = 'CallbacksGet'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.args = step_dict['args']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'callback_names', 'from': 'callback_names', 'by': 'ref', 'type': 'object'}]
            self.kwargs = dict()
            self.args = list()
            self.outputs = [{'name': 'pages', 'type': 'List'}]

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            if input_arg['by'] == 'ref':
                assert input_arg['from'] in pipeline_dict, '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        callback_names= None
        for input_arg in self.inputs:
            if input_arg['name'] == 'callback_names':
                if input_arg['by'] == 'ref':
                    callback_names = pipeline_dict[input_arg['from']]
                elif input_arg['by'] == 'val':
                    callback_names = input_arg['from']
        if callback_names is None:
            self.logger.exception('"callback_names" is missing from context')
            raise ValueError('"callback_names" is missing from context')

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['callback_names']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # run
        outputs = list()
        for callback_name in callback_names:
            # get callback from main function
            cb = mapping[callback_name]()
            # init callback with params
            outputs.append(cb(**kwargs))

        # Save outputs arguments
        if not isinstance(outputs, tuple):
            # single output - put in tuple
            outputs = (outputs,)
        for i_output, output_arg in enumerate(self.outputs):
            pipeline_dict[output_arg['name']] = outputs[i_output]
        return pipeline_dict

    @staticmethod
    def get_arguments():
        print('not available')
        # TODO
        return
        import inspect
        from ... import repositories
        signature = inspect.signature(repositories.Items.list)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
