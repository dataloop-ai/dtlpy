from behave import when, then
import time
import dtlpy as dl


@when(u'I delete current nodes and add dataset nodes to pipeline')
def step_impl(context):
    """
    Remove all nodes from pipeline
    Add dataset node#1 > dataset node#2 > connect them > Start pipeline
    Code-node#1
    """

    context.pipeline = context.project.pipelines.get(pipeline_name=context.pipeline_name)

    for node in context.pipeline.nodes:
        assert context.pipeline.nodes.remove(node.name), "TEST FAILED: Failed to delete node {}".format(node.name)

    dataset_node_1 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 2)
    )

    dataset_node_2 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(3, 3)
    )

    context.pipeline.nodes.add(dataset_node_1).connect(dataset_node_2)
    context.pipeline = context.pipeline.update()
    context.pipeline.install()

    time.sleep(5)


@then(u'Pipeline status is "{status}"')
def step_impl(context, status):
    try:
        context.pipeline = context.project.pipelines.get(pipeline_name=context.pipeline_name)
        assert context.pipeline.status == status
    except:
        print("TEST FAILED: Pipeline status expected: {} , Got: {}".format(status, context.pipeline.status))
        success, response = context.dl.client_api.gen_request(
            req_type="get",
            path="/compositions/{composition_id}".format(
                composition_id=context.pipeline.composition_id)
        )

        print("Error message: {}".format(response.json()['errorText']['message']))


@when(u'I update node input output to infinite loop')
def step_impl(context):
    try:
        context.pipeline.nodes.add(context.nodes[0])
        context.nodes.pop(0)

        context.pipeline.nodes[0].connect(context.pipeline.nodes[0])
        context.pipeline.update()
        context.error = None
    except Exception as e:
        context.error = e

