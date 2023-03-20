import time
import dtlpy as dl
import behave
import random


@behave.given(u'I create "{node_type}" node with params')
def step_impl(context, node_type):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    if node_type == "dataset":
        context.dataset_node = dl.DatasetNode(
            name=params.get('name', context.dataset.name),
            project_id=context.project.id,
            dataset_id=context.dataset.id,
            dataset_folder=params.get('folder', None),
            position=eval(params.get('position', "(1, 1)"))
        )

    context.nodes.append(context.dataset_node)


@behave.Given(u'I create pipeline with the name "{pipeline_name}"')
def step_impl(context, pipeline_name):
    context.pipeline = context.project.pipelines.create(name='{}-{}'.format(pipeline_name, random.randrange(1000, 10000)))
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I add and connect all nodes in list to pipeline entity')
def step_impl(context):
    assert context.nodes, "TEST FAILED: Nodes list is empty.{}".format(context.nodes)

    context.pipeline.nodes.add(context.nodes[0])
    context.nodes.pop(0)

    for i in range(len(context.nodes)):
        context.pipeline.nodes[i].connect(context.nodes[i])

    context.pipeline = context.pipeline.update()


@behave.when(u'I add trigger to first node with params')
def step_impl(context):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    context.filters = context.dl.Filters()
    for key, val in params.items():
        context.filters.add(field=key, values=val)

    context.pipeline.nodes[0].add_trigger(filters=context.filters)
    context.pipeline = context.pipeline.update()
