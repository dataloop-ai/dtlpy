import logging
from . import pipeline_step


class AnnotationsUploadStep(pipeline_step.PipelineStep):
    """
    Item upload step creator
    """

    def __init__(self, step_dict=None):
        super(AnnotationsUploadStep, self).__init__()
        self.name = 'AnnotationsUpload'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.outputs = step_dict['outputs']
            self.args = step_dict['args']
        else:
            self.inputs = [{'name': 'item', 'from': 'item', 'by': 'ref', 'type': 'object'},
                           {'name': 'annotations', 'from': 'annotations', 'by': 'ref', 'type': 'List'}]
            self.kwargs = {}
            self.outputs = []
            self.args = []

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        item_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'item']
        if len(item_from) != 1:
            self.logger.exception('"item" is missing from context')
            raise ValueError('"item" is missing from context')
        item = pipeline_dict.get(item_from[0])

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['item']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # run
        outputs = item.annotations.upload(**kwargs)

        # Save outputs arguments
        if not isinstance(outputs, tuple):
            # single output - put in tuple
            outputs = (outputs,)
        for i_output, output_arg in enumerate(self.outputs):
            pipeline_dict[output_arg['name']] = outputs[i_output]
        return pipeline_dict

    @staticmethod
    def get_arguments():
        import inspect
        from ... import repositories
        signature = inspect.signature(repositories.Items.upload)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
