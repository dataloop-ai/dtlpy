import logging
from . import pipeline_step


class PackagesProjectsUnpackStep(pipeline_step.PipelineStep):
    """
    Package from project unpack step
    """

    def __init__(self, step_dict=None):
        super(PackagesProjectsUnpackStep, self).__init__()
        self.name = 'PackagesProjectsUnpack'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.args = step_dict['args']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'platform_interface', 'from': 'platform_interface', 'by': 'ref', 'type': 'object'},
                           {'name': 'project_id', 'from': 'project_id', 'by': 'ref', 'type': 'object'},
                           {'name': 'package_name', 'from': 'package_name', 'by': 'ref', 'type': 'string'}]
            self.kwargs = {}
            self.args = []
            self.outputs = [{'name': 'package_path', 'type': 'string'}]

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        platform_interface_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'platform_interface']
        if len(platform_interface_from) != 1:
            self.logger.exception('"platform_interface" is missing from context')
            raise ValueError('"platform_interface" is missing from context')
        project_id_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'project_id']
        if len(project_id_from) != 1:
            self.logger.exception('"project_id" is missing from context')
            raise ValueError('"project_id" is missing from context')
        project_id = pipeline_dict.get(project_id_from[0])
        platform_interface = pipeline_dict.get(platform_interface_from[0])

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['project_id', 'platform_interface']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # run
        project = platform_interface.projects.get(project_id=project_id)
        outputs = project.packages.unpack(**kwargs)

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
        signature = inspect.signature(repositories.Packages.unpack)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
