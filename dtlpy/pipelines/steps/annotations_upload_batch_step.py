import logging
from . import pipeline_step


class AnnotationsUploadBatchStep(pipeline_step.PipelineStep):
    """
    Item upload step creator
    """

    def __init__(self, step_dict=None):
        super(AnnotationsUploadBatchStep, self).__init__()
        self.name = 'AnnotationsUploadBatch'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.outputs = step_dict['outputs']
            self.args = step_dict['args']
        else:
            self.inputs = [{'name': 'items', 'from': 'items', 'by': 'ref', 'type': 'List'},
                           {'name': 'annotations_list', 'from': 'annotations_list', 'type': 'List'}]
            self.kwargs = dict()
            self.outputs = list()
            self.args = list()

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        items_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'items']
        if len(items_from) != 1:
            self.logger.exception('"items" is missing from context')
            raise ValueError('"items" is missing from context')
        items_list = pipeline_dict.get(items_from[0])
        annotations_list_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'annotations_list']
        if len(annotations_list_from) != 1:
            msg = '"annotations_list" is missing from context'
            self.logger.exception(msg)
            raise ValueError(msg)
        annotations_list = pipeline_dict.get(annotations_list_from[0])

        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['items', 'annotations_list']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        outputs = list()
        for item, annotations in zip(items_list, annotations_list):
            kwargs['annotations'] = annotations
            # run
            outputs.append(item.annotations.upload(**kwargs))

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
