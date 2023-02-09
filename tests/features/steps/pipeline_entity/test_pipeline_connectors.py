from behave import when, then, given
import time
import dtlpy as dl


@when(u'I create a pipeline with code nodes with 2 outputs and code node with 2 inputs')
def step_impl(context):
    """
    Pipeline contain 2 code nodes with 2 outpus and 2 inputs
    Code-node#1 code node have 2 outputs - return item and dataset resources
    Code-node#2 code node have 2 inputs - get item and dataset resources
    """
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.pipeline_name = 'pipeline-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=context.pipeline_name)

    def run_1(item: dl.Item):
        dataset = item.dataset
        return item, dataset

    def run_2(item: dl.Item, dataset: dl.Dataset):
        assert item.dataset.id == dataset.id
        return item

    code_node_1 = dl.CodeNode(
        name="code-1",
        position=(1, 1),
        project_id=context.project.id,
        method=run_1,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEM,
                                   name='item',
                                   display_name='item'),
                 dl.PipelineNodeIO(input_type=dl.PackageInputType.DATASET,
                                   name='dataset',
                                   display_name='dataset')
                 ]
    )

    code_node_2 = dl.CodeNode(
        name="code-2",
        position=(2, 2),
        project_id=context.project.id,
        method=run_2,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(input_type=dl.PackageInputType.ITEM,
                                  name='item',
                                  display_name='item'),
                dl.PipelineNodeIO(input_type=dl.PackageInputType.DATASET,
                                  name='dataset',
                                  display_name='dataset')
                ]
    )

    filters = context.dl.Filters()
    filters.add(field='datasetId', values=context.dataset.id)
    context.pipeline.nodes.add(code_node_1)
    context.pipeline.nodes[0].connect(node=code_node_2, target_port=code_node_2.inputs[0], source_port=code_node_1.outputs[0])
    context.pipeline.nodes[0].connect(node=code_node_2, target_port=code_node_2.inputs[1], source_port=code_node_1.outputs[1])
    code_node_1.add_trigger(filters=filters)

    context.pipeline = context.pipeline.update()
    context.pipeline.install()

    time.sleep(5)
