from behave import when, then, given
import time
import dtlpy as dl


@when(u'I create custom pipeline for code node with progress.update(action="{action_input}")')
def step_impl(context, action_input):
    """
    Pipeline contain 3 code nodes
    Code-node#1 contain progress.update(action='') and has 2 node outputs with action "first-output" and action "second-output"
    Code-node#2 connect to output[0] - action "first-output"
    Code-node#3 connect to output[1] - action "second-output"
    """
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.pipeline_name = 'pipeline-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=context.pipeline_name, project_id=context.project.id)

    if "first" in action_input:
        def run_1(item, progress):
            progress.update(action="first-output")

            return item
    elif "second" in action_input:
        def run_1(item, progress):
            progress.update(action="second-output")

            return item
    else:
        assert False, "action_input Should be 'first-output' OR 'second-output'"

    def run_2(item):
        return item

    def run_3(item):
        assert False, "Should not pass to code-node-3"
        return item

    code_node_1 = dl.CodeNode(
        name="code-1",
        position=(1, 2),
        project_id=context.project.id,
        method=run_1,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEM,
                                   name='item',
                                   display_name='item',
                                   actions=['first-output', 'second-output'])
                 ]
    )

    code_node_2 = dl.CodeNode(
        name="code-2",
        position=(2, 1),
        project_id=context.project.id,
        method=run_2,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEM,
                                   name='item',
                                   display_name='item')]
    )

    code_node_3 = dl.CodeNode(
        name="code-3",
        position=(2, 3),
        project_id=context.project.id,
        method=run_3,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEM,
                                   name='item',
                                   display_name='item')]
    )

    filters = context.dl.Filters()
    filters.add(field='datasetId', values=context.dataset.id)
    context.pipeline.nodes.add(code_node_1).connect(node=code_node_2, source_port=code_node_1.outputs[0], action="first-output")
    context.pipeline.nodes[0].connect(node=code_node_3, source_port=code_node_1.outputs[0], action="second-output")
    code_node_1.add_trigger(filters=filters)

    context.pipeline = context.pipeline.update()
    context.pipeline.install()

    time.sleep(5)
