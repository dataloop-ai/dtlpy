import logging
from . import pipeline_step


class SessionsArtifactsDownloadStep(pipeline_step.PipelineStep):
    """
    Artifact download step
    """

    def __init__(self, step_dict=None):
        super(SessionsArtifactsDownloadStep, self).__init__()
        self.name = 'SessionsArtifactsDownload'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'session', 'from': 'session', 'type': 'object'}]
            self.kwargs = {}
            self.outputs = [{'name': 'filename', 'type': 'object'}]

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        session_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'session']
        if len(session_from) != 1:
            self.logger.exception('"session" is missing from context')
            raise ValueError('"session" is missing from context')
        session = pipeline_dict.get(session_from[0])

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['session']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # Run step
        outputs = session.artifacts.download(**kwargs)

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
        signature = inspect.signature(repositories.Artifacts.download)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
