from behave import given, when, then
import random
import string
import time


def random_5_chars():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'


@given(u'a pipeline with task node that receives many to one input')
def step_impl(context):
    pipe_json = {
        "name": "Test Task Many to One - {}".format(random_5_chars()),
        "projectId": context.project.id,
        "nodes": [
            {
                "id": "e6a4e030-3edf-4ec2-a348-cf048970fd55",
                "inputs": [
                    {
                        "portId": "47ce56b1-96e7-4d52-b6bf-4786f957575e",
                        "nodeId": "47ce56b1-96e7-4d52-b6bf-4786f957575e",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "f3f22654-cb08-4da6-aa8e-e9e71bc7db38",
                        "nodeId": "f3f22654-cb08-4da6-aa8e-e9e71bc7db38",
                        "type": "Item[]",
                        "name": "items",
                        "displayName": "items",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 9872.3515625,
                        "y": 9824,
                        "z": 0
                    },
                    "componentGroupName": "automation",
                    "codeApplicationName": "split",
                    "repeatable": True
                },
                "name": "split",
                "type": "code",
                "namespace": {
                    "functionName": "run",
                    "projectName": context.project.name,
                    "serviceName": "split",
                    "moduleName": "code_module",
                    "packageName": "split"
                },
                "projectId": context.project.id,
                "config": {
                    "package": {
                        "code": "import dtlpy as dl\n\nclass ServiceRunner:\n\n    def run(self, item):\n        return item.dataset.items.list().items\n",
                        "name": "run",
                        "type": "code",
                        "codebase": {
                            "type": "item"
                        }
                    }
                }
            },
            {
                "id": "325ca877-578c-48e5-b94c-d3cc39853e5b",
                "inputs": [
                    {
                        "portId": "63de9478-ccd2-4840-808a-1ac550c43da3",
                        "nodeId": "63de9478-ccd2-4840-808a-1ac550c43da3",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "028d2311-1421-47ff-bcfe-e2e0dacb76d9",
                        "nodeId": "028d2311-1421-47ff-bcfe-e2e0dacb76d9",
                        "type": "Item",
                        "name": "item",
                        "displayName": "Complete",
                        "actions": [
                            "completed",
                            "discard"
                        ],
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10222.3515625,
                        "y": 9858,
                        "z": 0
                    },
                    "recipeTitle": context.dataset.name + " - Default recipe",
                    "recipeId": context.dataset.get_recipe_ids()[0],
                    "taskType": "annotation",
                    "datasetId": context.dataset.id,
                    "taskOwner": context.dataset.creator,
                    "workload": [
                        {
                            "assigneeId": context.dataset.creator,
                            "load": 100
                        }
                    ],
                    "maxBatchWorkload": 7,
                    "batchSize": 5,
                    "priority": 2,
                    "componentGroupName": "workflow",
                    "repeatable": True,
                    "dueDate": 0,
                    "groups": [

                    ]
                },
                "name": "Labeling",
                "type": "task",
                "namespace": {
                    "functionName": "move_to_task",
                    "projectName": "DataloopTasks",
                    "serviceName": "pipeline-utils",
                    "moduleName": "default_module",
                    "packageName": "pipeline-utils"
                }
            },
            {
                "id": "585fc85b-69a1-4dcd-9f63-d2b4f303fded",
                "inputs": [
                    {
                        "portId": "2058bd88-dc64-481f-9943-a1d809db2144",
                        "nodeId": "2058bd88-dc64-481f-9943-a1d809db2144",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "a60b1a10-9dc3-4442-a575-0a2007d68bd9",
                        "nodeId": "a60b1a10-9dc3-4442-a575-0a2007d68bd9",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10632.3515625,
                        "y": 9890,
                        "z": 0
                    },
                    "componentGroupName": "automation",
                    "codeApplicationName": "done",
                    "repeatable": True
                },
                "name": "done",
                "type": "code",
                "namespace": {
                    "functionName": "run",
                    "projectName": context.project.name,
                    "serviceName": "done",
                    "moduleName": "code_module",
                    "packageName": "done"
                },
                "projectId": context.project.id,
                "config": {
                    "package": {
                        "code": "import dtlpy as dl\n\nclass ServiceRunner:\n\n    def run(self, item):\n        return item\n",
                        "name": "run",
                        "type": "code",
                        "codebase": {
                            "type": "item"
                        }
                    }
                }
            }
        ],
        "connections": [
            {
                "src": {
                    "nodeId": "325ca877-578c-48e5-b94c-d3cc39853e5b",
                    "portId": "028d2311-1421-47ff-bcfe-e2e0dacb76d9"
                },
                "tgt": {
                    "nodeId": "585fc85b-69a1-4dcd-9f63-d2b4f303fded",
                    "portId": "2058bd88-dc64-481f-9943-a1d809db2144"
                },
                "condition": "{}",
                "action": "completed"
            },
            {
                "src": {
                    "nodeId": "e6a4e030-3edf-4ec2-a348-cf048970fd55",
                    "portId": "f3f22654-cb08-4da6-aa8e-e9e71bc7db38"
                },
                "tgt": {
                    "nodeId": "325ca877-578c-48e5-b94c-d3cc39853e5b",
                    "portId": "63de9478-ccd2-4840-808a-1ac550c43da3"
                },
                "condition": "{}"
            }
        ],
        "startNodes": [
            {
                "nodeId": "e6a4e030-3edf-4ec2-a348-cf048970fd55",
                "type": "root",
                "id": "d6771d5a-b457-42f3-b881-944226676110"
            }
        ]
    }
    context.pipeline = context.project.pipelines.create(
        pipeline_json=pipe_json,
        name=pipe_json['name'],
        project_id=context.project.id
    )


@given(u'I execute the pipeline on item')
def step_impl(context):
    context.execution = context.pipeline.execute(
        execution_input={'item': context.item.id}
    )


@when(u'I set status on some of the input items')
def step_impl(context):
    composition_id = context.pipeline.composition_id
    context.composition = context.project.compositions.get(composition_id=composition_id)
    composition_task = context.composition['tasks'][0]
    context.task = context.project.tasks.get(task_id=composition_task['state']['taskId'])
    dataset_items = context.dataset.items.list().items
    task_items = context.task.get_items().items
    while len(task_items) < len(dataset_items):
        task_items = context.task.get_items().items
        time.sleep(1)

    for item in task_items[:2]:
        item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id)
    cycle: context.dl.PipelineExecution = context.pipeline.pipeline_executions.list().items[0]
    last_node = cycle.nodes[-1]
    max_wait = 60 * 3
    start = time.time()
    while last_node.status == 'pending':
        if time.time() - start > max_wait:
            break
        cycle: context.dl.PipelineExecution = context.pipeline.pipeline_executions.list().items[0]
        last_node = cycle.nodes[-1]
        time.sleep(1)


@then(u'cycle should be inProgress and task node should be inProgress')
def step_impl(context):
    cycle: context.dl.PipelineExecution = context.pipeline.pipeline_executions.list().items[0]
    task_node = [n for n in cycle.nodes if n.node_type == 'task'][0]
    last_node = cycle.nodes[-1]
    assert cycle.status == 'in-progress'
    assert task_node.status == 'in-progress'
    assert last_node.status != 'pending'


@when(u'I set status on all input items')
def step_impl(context):
    dataset_items = context.dataset.items.list().items
    for item in dataset_items:
        exist_status = item.status(task_id=context.task.id)
        if exist_status != context.dl.ItemStatus.COMPLETED:
            item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id)


@then(u'cycle should be completed and task node should be completed')
def step_impl(context):
    cycle_success = False
    task_node_success = False
    max_wait = 60 * 3
    start = time.time()
    while not cycle_success or not task_node_success:
        if time.time() - start > max_wait:
            break
        cycle: context.dl.PipelineExecution = context.pipeline.pipeline_executions.list().items[0]
        task_node = [n for n in cycle.nodes if n.node_type == 'task'][0]
        if cycle.status == 'success':
            cycle_success = True
        if task_node.status == 'success':
            task_node_success = True
        time.sleep(1)
    assert cycle_success, 'Cycle did not transition to success'
    assert task_node_success, 'Task node did not transition to success'

