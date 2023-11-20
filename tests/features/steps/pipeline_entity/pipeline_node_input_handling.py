import behave
import dtlpy as dl


@behave.when(u'I build a pipeline where the second node handles missing input')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='test_pipeline', project_id=context.project.id)

    def run(string):
        if string != 'return_none':
            return string

    context.root = dl.CodeNode(
        name='root',
        position=(2, 2),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )],
        outputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )]
    )

    def run1(string):
        if string is None:
            raise ValueError("required input is missing")
        return string

    context.n1 = dl.CodeNode(
        name='n1',
        position=(3, 2),
        project_id=context.project.id,
        method=run1,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string",
            default_value="default_string"
        )],
        outputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )]
    )

    context.pipeline.nodes.add(node=context.root).connect(node=context.n1)
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I build a pipeline where the second node does not handle missing input')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='test_pipeline', project_id=context.project.id)

    def run(string):
        if string != 'return_none':
            return string

    context.root = dl.CodeNode(
        name='root',
        position=(2, 2),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )],
        outputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )]
    )

    def run1(string):
        if string is None:
            raise ValueError("required input is missing")
        return string

    context.n1 = dl.CodeNode(
        name='n1',
        position=(3, 2),
        project_id=context.project.id,
        method=run1,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )],
        outputs=[dl.PipelineNodeIO(
            input_type=dl.PackageInputType.STRING,
            name="string",
            display_name="string"
        )]
    )

    context.pipeline.nodes.add(node=context.root).connect(node=context.n1)
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I execute pipeline with input type: "{input_type}" and input value: "{input_value}"')
def step_impl(context, input_type, input_value):
    value = input_value
    if input_value == "None":
        value = None

    execution_input = list()
    if input_type == dl.PackageInputType.ITEM:
        execution_input.append(context.dl.FunctionIO(
            type=dl.PackageInputType.ITEM,
            value={'item_id': value},
            name='item'))
    elif input_type == dl.PackageInputType.STRING:
        execution_input.append(context.dl.FunctionIO(
            type=dl.PackageInputType.STRING,
            value=value,
            name='string'))
    context.execution = context.pipeline.execute(
        execution_input=execution_input)


@behave.when(u'I execute pipeline without input')
def step_impl(context):
    context.execution = context.pipeline.execute(
        execution_input={})


@behave.then(u'Cycle "{cycle_number}" node "{node_number}" execution "{execution_number}" single output is: "{expected_output_value}"')
def step_impl(context, cycle_number, node_number, execution_number, expected_output_value):
    cycle_index = int(cycle_number) - 1
    node_index = int(node_number) - 1
    execution_index = int(execution_number) - 1
    cycle = context.cycles[cycle_index]
    node_id = cycle.nodes[node_index].node_id
    execution_id = cycle.executions[node_id][execution_index]['_id']
    execution = dl.executions.get(execution_id=execution_id)
    output_value = execution.output
    assert expected_output_value == output_value, "Execution output was {} where {} was expected".format(output_value, expected_output_value)


@behave.then(u'Cycle "{cycle_number}" status is "{expected_cycle_status}"')
def step_impl(context, cycle_number, expected_cycle_status ):
    cycle_index = int(cycle_number) - 1
    cycle = context.cycles[cycle_index]
    assert cycle.status == expected_cycle_status, "Cycle status is {} where {} was expected".format(cycle.status, expected_cycle_status)