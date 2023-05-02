from behave import when, then, given
import time
import dtlpy as dl
import json
import random
import os


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


def generate_pipeline_json(context, pipeline_json):
    pipeline_json['name'] = 'json-pipe-{}'.format(random.randrange(10000, 100000))
    pipeline_json['creator'] = context.dl.info()['user_email']
    pipeline_json['projectId'] = context.project.id
    pipeline_json['orgId'] = context.project.org['id']

    for node in pipeline_json['nodes']:
        node['projectId'] = context.project.id

    datasets_node = [node for node in pipeline_json['nodes'] if node['type'] == 'storage']
    for node in datasets_node:
        node['name'] = context.dataset.name
        node['metadata']["datasetId"] = context.dataset.id

    return pipeline_json


@given(u'I create pipeline from json in path "{path}"')
def step_impl(context, path):
    test_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    with open(test_path, 'r') as pipeline_path:
        pipeline_json = json.load(pipeline_path)

    pipeline_payload = generate_pipeline_json(
        context=context,
        pipeline_json=pipeline_json
    )

    context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_payload)
    context.to_delete_pipelines_ids.append(context.pipeline.id)
