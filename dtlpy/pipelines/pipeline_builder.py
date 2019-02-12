import yaml
from .steps import PipelineStage


class PipelineBuilder(object):
    """
    Pipeline builder
    """

    def __init__(self):
        self.inputs = list()
        self.stages = list()

    @property
    def n_stages(self):
        return len(self.stages)

    def add_stage(self, stage):
        if isinstance(stage, dict):
            stage = PipelineStage(stage_dict=stage)
        self.stages.append(stage)

    def reset(self):
        self.stages = list()

    def from_dict(self, pipeline_dict):
        self.inputs = pipeline_dict['inputs']
        self.stages = [PipelineStage(stage_dict) for stage_dict in pipeline_dict['stages']]

    def from_file(self, filename):
        with open(filename, 'r') as f:
            pipeline_dict = yaml.safe_load(f)
        self.from_dict(pipeline_dict=pipeline_dict)

    def to_file(self, filename):
        stages = self.stages
        stages_list = list()
        for stage in stages:
            stage_dict = stage.to_dict()
            steps = [step.to_dict() for step in stage.steps]
            stage_dict['steps'] = steps
            stages_list.append(stage_dict)

        pipeline_dict = {'inputs': self.inputs, 'stages': stages_list}
        with open(filename, 'w') as f:
            yaml.safe_dump(pipeline_dict, f, default_flow_style=False)

    def get_context(self):
        input_arg_names = list()
        needed_arg_names = list()
        output_arg_names = list()
        for stage in self.stages:
            for step in stage.steps:
                for input_arg in step.inputs:
                    if input_arg['from'] not in input_arg_names:
                        input_arg_names.append(input_arg['from'])
                for output_arg in step.outputs:
                    if output_arg['name'] not in output_arg_names:
                        output_arg_names.append(output_arg['name'])
        for arg in input_arg_names:
            if arg not in output_arg_names:
                needed_arg_names.append(arg)
        return needed_arg_names
