import logging
from . import pipeline_step


class ItemsDownloadStep(pipeline_step.PipelineStep):
    """
    Item download step creator
    """

    def __init__(self, step_dict=None):
        super(ItemsDownloadStep, self).__init__()
        self.name = 'ItemsDownload'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.args = step_dict['args']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'dataset', 'from': 'dataset', 'by': 'ref', 'type': 'object'},
                           {'name': 'item_id', 'from': 'item_id', 'by': 'ref', 'type': 'string'}]
            self.kwargs = {'save_locally': True}
            self.args = list()
            self.outputs = [{'name': 'filepath', 'type': 'string'}]

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']
            # get input item 'name' from 'from'

        # prepare
        dataset_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'dataset']
        if len(dataset_from) != 1:
            self.logger.exception('"dataset" is missing from context')
            raise ValueError('"dataset" is missing from context')
        dataset = pipeline_dict.get(dataset_from[0])

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['dataset']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # run
        outputs = dataset.items.download(**kwargs)

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
        signature = inspect.signature(repositories.Items.download)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
