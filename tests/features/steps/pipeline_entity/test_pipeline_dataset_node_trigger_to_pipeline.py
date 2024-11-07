import random
import string
import time

from behave import given, when, then


def find_dataset_node(context):
    nodes = context.pipeline.nodes
    return next((node for node in nodes if node.node_type == 'storage'), None)


def get_item_executions(context):
    return context.item.resource_executions.list().items_count


@then(u'The dataset node is marked as triggered')
def step_impl(context):
    node = find_dataset_node(context)
    assert node is not None, "TEST FAILED: Dataset node not found"
    trigger_to_pipeline = node.metadata.get('triggerToPipeline')
    assert trigger_to_pipeline is not None, "TEST FAILED: Dataset node does not have triggerToPipeline in the metadata"
    assert trigger_to_pipeline.get('active'), "TEST FAILED: Dataset node is not marked as active"
    assert trigger_to_pipeline.get('triggered'), "TEST FAILED: Dataset node is not marked as triggered"


@then(u'The dataset node is assigned with a command id')
def step_impl(context):
    node = find_dataset_node(context)
    assert node is not None, "TEST FAILED: Dataset node not found"
    trigger_to_pipeline = node.metadata.get('triggerToPipeline')
    assert trigger_to_pipeline is not None, "TEST FAILED: Dataset node does not have triggerToPipeline in the metadata"
    assert trigger_to_pipeline.get('commandId') is not None, "TEST FAILED: Dataset node is not assigned with a " \
                                                             "command id "


@then(u'The dataset node has data_filters')
def step_impl(context):
    node = find_dataset_node(context)
    assert node is not None, "TEST FAILED: Dataset node not found"
    trigger_to_pipeline = node.metadata.get('triggerToPipeline')
    assert trigger_to_pipeline is not None, "TEST FAILED: Dataset node does not have triggerToPipeline in the metadata"
    assert trigger_to_pipeline.get('filter') is not None, "TEST FAILED: Dataset node is not assigned with a filter"
    assert node.data_filters is not None, "TEST FAILED: Dataset node is not assigned with a filter"


@then(u'The uploaded item has "{num}" executions')
def step_impl(context, num):
    time.sleep(2)
    executions = get_item_executions(context)
    assert executions == int(num), f"TEST FAILED: Item has {executions} executions"


@given(u'I have a pipeline with 2 dataset nodes with variables and triggerToPipeline=true')
def step_impl(context):
    pipeline_json = {
        "nodes": [
            {
                "id": "13898b44-7a61-4684-a172-90196b2c9fbd",
                "inputs": [
                    {
                        "portId": "70c69fbc-e705-4892-abba-04325c3bba4e",
                        "nodeId": "70c69fbc-e705-4892-abba-04325c3bba4e",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "92529eee-31c9-4b61-82e4-722d9862f22b",
                        "nodeId": "92529eee-31c9-4b61-82e4-722d9862f22b",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10280,
                        "y": 10043,
                        "z": 0
                    },
                    "componentGroupName": "data",
                    "repeatable": True,
                    "variableDataset": "dataset",
                    "triggerToPipeline": {
                        "active": True
                    }
                },
                "name": "dataset",
                "type": "storage",
                "namespace": {
                    "functionName": "clone_item",
                    "projectName": "DataloopTasks",
                    "serviceName": "pipeline-utils",
                    "moduleName": "default_module",
                    "packageName": "pipeline-utils"
                },
                "projectId": context.project.id
            },
            {
                "id": "057af07a-5455-462e-a942-5f3f015e7eb7",
                "inputs": [
                    {
                        "portId": "edb87533-59da-40b7-b8a8-28cb95769372",
                        "nodeId": "edb87533-59da-40b7-b8a8-28cb95769372",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "3df23f62-4581-452e-9595-31ef50ed5c40",
                        "nodeId": "3df23f62-4581-452e-9595-31ef50ed5c40",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10599,
                        "y": 10098,
                        "z": 0
                    },
                    "componentGroupName": "data",
                    "repeatable": True,
                    "variableDataset": "dataset"
                },
                "name": "dataset",
                "type": "storage",
                "namespace": {
                    "functionName": "clone_item",
                    "projectName": "DataloopTasks",
                    "serviceName": "pipeline-utils",
                    "moduleName": "default_module",
                    "packageName": "pipeline-utils"
                },
                "projectId": context.project.id
            }
        ],
        "connections": [
            {
                "src": {
                    "nodeId": "13898b44-7a61-4684-a172-90196b2c9fbd",
                    "portId": "92529eee-31c9-4b61-82e4-722d9862f22b"
                },
                "tgt": {
                    "nodeId": "057af07a-5455-462e-a942-5f3f015e7eb7",
                    "portId": "edb87533-59da-40b7-b8a8-28cb95769372"
                },
                "condition": "{}"
            }
        ],
        "startNodes": [
            {
                "nodeId": "13898b44-7a61-4684-a172-90196b2c9fbd",
                "type": "root",
                "id": "ee209df9-7007-4e33-8433-225656093c15"
            }
        ],
        "variables": [
            {
                "name": "dataset",
                "type": "Dataset",
                "value": context.dataset.id
            }
        ]
    }

    context.pipeline = context.project.pipelines.create(
        pipeline_json=pipeline_json,
        name="triggerToPipeline-var{}".format(
            ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + 'a'
        )
    )

@then(u'All dataset items should run')
def step_impl(context):
    start = time.time()
    timeout = 60
    success = False
    item_count = context.dataset.items.list().items_count

    while time.time() - start < timeout:
        cycle_count = context.pipeline.pipeline_executions.list().items_count
        if cycle_count == item_count:
            success = True
            break

    assert success, 'Pipeline did not run all items'