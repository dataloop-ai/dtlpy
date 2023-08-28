from behave import when, then, given
import time
import dtlpy as dl


@when(u'I create custom pipeline for code node with progress.update(action="{action_input}")')
def step_impl(context, action_input):
    """
    Pipeline contain 3 code nodes
    Code-node#1 contain progress.update(action='') and has 2 node outputs with action "first-output" and action "second-output"
    Dataset-node#1 connect to output[0] - action "first-output"
    Dataset-node#2 connect to output[1] - action "second-output"
    """
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.pipeline_name = 'pipeline-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=context.pipeline_name, project_id=context.project.id)

    if "first" in action_input:
        def run_1(item, progress):
            progress.update(action="first-output")
            import time
            time.sleep(1)
            return item
    elif "second" in action_input:
        def run_1(item, progress):
            progress.update(action="second-output")
            import time
            time.sleep(1)
            return item
    else:
        assert False, "action_input Should be 'first-output' OR 'second-output'"

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

    dataset_node_1 = dl.DatasetNode(
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        name="dataset-1",
        position=(2, 1)
    )

    dataset_node_2 = dl.DatasetNode(
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        name="dataset-2",
        position=(2, 3)
    )

    filters = context.dl.Filters()
    filters.add(field='datasetId', values=context.dataset.id)
    context.pipeline.nodes.add(code_node_1).connect(node=dataset_node_1, source_port=code_node_1.outputs[0],
                                                    action="first-output")
    context.pipeline.nodes[0].connect(node=dataset_node_2, source_port=code_node_1.outputs[0], action="second-output")
    code_node_1.add_trigger(filters=filters)

    context.pipeline = context.pipeline.update()
    context.pipeline.install()

    time.sleep(5)
