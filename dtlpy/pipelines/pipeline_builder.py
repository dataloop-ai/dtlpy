import json
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
            pipeline_dict = json.load(f)
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
            json.dump(pipeline_dict, f, indent=4)

    def get_context(self):
        input_arg_names = list()
        needed_arg_names = list()
        output_arg_names = list()

        # go over all stage
        for stage in self.stages:

            # take generators output
            for gen in stage.generators:
                for output_arg in gen['outputs']:
                    if output_arg['name'] not in output_arg_names:
                        output_arg_names.append(output_arg['name'])

            for step in stage.steps:
                # go over all steps in stage
                for input_arg in step.args:
                    # go over all inputs in inputs list
                    if 'by' in input_arg:
                        if input_arg['by'] == 'ref':
                            add_arg = True
                        else:
                            add_arg = False
                    else:
                        add_arg = True
                    if add_arg and input_arg['from'] not in input_arg_names:
                        input_arg_names.append(input_arg['from'])

                # go over all steps in stage
                for input_arg in step.inputs:
                    # go over all inputs in inputs list
                    if 'by' in input_arg:
                        if input_arg['by'] == 'ref':
                            add_arg = True
                        else:
                            add_arg = False
                    else:
                        add_arg = True
                    if add_arg and input_arg['from'] not in input_arg_names:
                        input_arg_names.append(input_arg['from'])
                # add outputs
                for output_arg in step.outputs:
                    if output_arg['name'] not in output_arg_names:
                        output_arg_names.append(output_arg['name'])
        for arg in input_arg_names:
            if arg not in output_arg_names:
                needed_arg_names.append(arg)
        return needed_arg_names
