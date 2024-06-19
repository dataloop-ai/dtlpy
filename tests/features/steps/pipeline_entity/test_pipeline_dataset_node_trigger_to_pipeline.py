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
