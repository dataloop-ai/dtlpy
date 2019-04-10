import abc


class PipelineStep(abc.ABC):
    """
    Step creator
    """

    def __init__(self):
        # default
        self.func = None
        self.kwargs = dict()
        self.args = dict()
        self.outputs = list()
        self.inputs = list()
        self.name = ''
        self.method_name = None
        self.type = ''

    def load_method_from_class(self, cls, method_name):
        try:
            method = getattr(cls, method_name)
        except AttributeError:
            raise NotImplementedError(
                "Class `{}` does not implement `{}`".format(cls.__class__.__name__, method_name))
        return method

    def execute(self, pipeline_dict):
        ############################
        # input arguments for step #
        ############################
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']
            # get input item 'name' from 'from'
            self.kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]
        ############
        # Run step #
        ############
        outputs = self.func(**self.kwargs)
        ##########################
        # Save outputs arguments #
        ##########################
        if outputs is not None:
            if not isinstance(outputs, tuple):
                # single output - put in tuple
                outputs = (outputs,)
            for i_output, output_arg in enumerate(self.outputs):
                pipeline_dict[output_arg['name']] = outputs[i_output]
        return pipeline_dict

    def inputs_sanity(self):
        for i_input in range(len(self.inputs)):
            if 'name' not in self.inputs[i_input]:
                raise ValueError('missing "name" from input: %s' % self.inputs[i_input])
            if 'from' not in self.inputs[i_input]:
                raise ValueError('missing "from" from input: %s' % self.inputs[i_input])
            if 'type' not in self.inputs[i_input]:
                raise ValueError('missing "type" from input: %s' % self.inputs[i_input])
            if 'by' not in self.inputs[i_input]:
                raise ValueError('missing "by" from input: %s' % self.inputs[i_input])

    def to_dict(self):
        """
        Generate the dictionary required to add this step to a pipeline stage
        """
        self.inputs_sanity()

        step = {'name': self.name,
                'inputs': self.inputs,
                'outputs': self.outputs,
                'kwargs': self.kwargs,
                'args': self.args,
                'type': self.type,
                'method_name': self.method_name}
        return step
