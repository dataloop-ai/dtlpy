import copy
import random
import time

import behave
import dtlpy as dl

pipeline_json = {
    "nodes": [
        {
            "id": "021f90cf-65f8-4f61-a1a2-4775e3bff685",
            "inputs": [
                {
                    "portId": "dd83b5f7-ffac-446e-b65a-8201e0328086",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "outputs": [
                {
                    "portId": "572b01df-e336-4f91-b4e3-458d1e79f532",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "metadata": {
                "position": {
                    "x": 51.90174865722656,
                    "y": 91.95087432861328,
                    "z": 0
                },
                "repeatable": True
            },
            "name": "code",
            "type": "code",
            "namespace": {
                "functionName": "run",
                "projectName": "SoS",
                "serviceName": "code-vuhtoxin52",
                "moduleName": "code_module",
                "packageName": "code-h3np603t56"
            },
            "projectId": "99d634a1-89bf-4d69-b201-807a29140c76",
            "config": {
                "package": {
                    "code": "import dtlpy as dl\n\nclass ServiceRunner:\n\n    def run(self, item):\n        return item\n",
                    "name": "run",
                    "type": "code"
                }
            }
        },
        {
            "id": "4a8bb1f9-7eb5-484a-8603-773d097f222b",
            "inputs": [
                {
                    "portId": "0a6b4481-efee-4cfa-b0cd-ffd42312a49f",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "outputs": [
                {
                    "portId": "c7bdac4e-0a3c-4bf0-9e45-311e23b3dd5a",
                    "type": "Task",
                    "name": "completed",
                    "displayName": "completed",
                    "color": "#14a182",
                    "actions": ["completed"]
                },
                {
                    "portId": "fc09ca5d-9a13-438b-993a-5518dc67b045",
                    "type": "Assignment",
                    "name": "completed",
                    "displayName": "done",
                    "color": "#69f4ef",
                    "actions": ["done"]
                },
                {
                    "portId": "ee8bbdf2-0e33-4688-af5c-800d88c583d0",
                    "type": "Item",
                    "name": "item",
                    "displayName": "completed",
                    "color": "#d004e4",
                    "actions": ["completed", "discard"]
                }
            ],
            "metadata": {
                "position": {
                    "x": 344,
                    "y": 87,
                    "z": 0
                },
                "recipeTitle": "Text Default Recipe",
                "recipeId": "628e3fa8b7bca61b1fa9cd3b",
                "taskType": "annotation",
                "datasetId": "628e3fa8e2a1bf337dee0c41",
                "taskOwner": "datalooptester123@gmail.com",
                "workload": [
                    {
                        "assigneeId": "matan305@bot.ai",
                        "load": 100
                    }
                ],
                "priority": 2,
                "repeatable": True,
                "dueDate": 1664744400000
            },
            "name": "First Task",
            "type": "task",
            "namespace": {
                "functionName": "move_to_task",
                "projectName": "DataloopTasks",
                "serviceName": "pipeline-utils",
                "moduleName": "default_module",
                "packageName": "pipeline-utils"
            },
            "projectId": "f8a4b8ce-5ff3-4386-84dc-1bda3a5bc92a"
        },
        {
            "id": "039c747d-6ec3-4fbb-8090-6134ecc78ae6",
            "inputs": [
                {
                    "portId": "0b357d4b-7e60-47a2-922e-7a22a4d7d6fc",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "outputs": [
                {
                    "portId": "a6a3115e-7678-4f6a-b39b-2dd9f54d554f",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "metadata": {
                "position": {
                    "x": 700,
                    "y": 89,
                    "z": 0
                },
                "repeatable": True
            },
            "name": "run",
            "type": "function",
            "namespace": {
                "functionName": "run",
                "projectName": "SoS",
                "serviceName": "custom-webm-converter-service",
                "moduleName": "webm_module",
                "packageName": "custom-webm-converter"
            },
            "projectId": "99d634a1-89bf-4d69-b201-807a29140c76"
        },
        {
            "id": "488d660b-9c81-4f12-ad38-7a57bcd3346c",
            "inputs": [
                {
                    "portId": "5a389b74-077f-4cde-a702-11775398bdb1",
                    "type": "Task",
                    "name": "task",
                    "displayName": "task"
                }
            ],
            "outputs": [],
            "metadata": {
                "position": {
                    "x": 698,
                    "y": 209,
                    "z": 0
                },
                "repeatable": True
            },
            "name": "Task Completed",
            "type": "code",
            "namespace": {
                "functionName": "run",
                "projectName": "SoS",
                "serviceName": "task-completed-hhos7jqgjf",
                "moduleName": "code_module",
                "packageName": "task-completed-7d6o2dygao"
            },
            "projectId": "99d634a1-89bf-4d69-b201-807a29140c76",
            "config": {
                "package": {
                    "code": "import dtlpy as dl\n\nclass ServiceRunner:\n\n    def run(self, task):\n        return task\n",
                    "name": "run",
                    "type": "code"
                }
            }
        },
        {
            "id": "967edc32-1eb3-4cfb-b127-8c3be9005726",
            "inputs": [
                {
                    "portId": "82dd52bc-7bc4-4baa-8f2c-8654022625e5",
                    "type": "Assignment",
                    "name": "assignment",
                    "displayName": "assignment"
                }
            ],
            "outputs": [],
            "metadata": {
                "position": {
                    "x": 698,
                    "y": 323,
                    "z": 0
                },
                "repeatable": True
            },
            "name": "Assignment Completed",
            "type": "code",
            "namespace": {
                "functionName": "run",
                "projectName": "SoS",
                "serviceName": "assignment-completed-d7gd40q8xgf",
                "moduleName": "code_module",
                "packageName": "assignment-completed-te50uh5d78"
            },
            "projectId": "99d634a1-89bf-4d69-b201-807a29140c76",
            "config": {
                "package": {
                    "code": "import dtlpy as dl\n\nclass ServiceRunner:\n\n    def run(self, assignment):\n        return assignment\n",
                    "name": "run",
                    "type": "code"
                }
            }
        },
        {
            "id": "0d811e02-aeea-475e-9514-9b497e215cab",
            "inputs": [
                {
                    "portId": "f7032c2a-f568-4971-ab7b-36c89a5d6e00",
                    "type": "Item",
                    "name": "item",
                    "displayName": "item"
                }
            ],
            "outputs": [
                {
                    "portId": "05177336-3e3b-4b5d-be42-f9d08925f52a",
                    "type": "Item",
                    "name": "item",
                    "displayName": "Complete",
                    "actions": ["completed", "discard"]

                }
            ],
            "metadata": {
                "position": {
                    "x": 1017,
                    "y": 89,
                    "z": 0
                },
                "recipeTitle": "Analytics2.0 Default Recipe",
                "recipeId": "622096f30e37e67e34caeac9",
                "taskType": "annotation",
                "datasetId": "622096f38c7c3254e470e9a0",
                "taskOwner": "datalooptester123@gmail.com",
                "workload": [
                    {
                        "assigneeId": "luhupabo@ryteto.me",
                        "load": 100
                    }
                ],
                "priority": 2,
                "repeatable": True,
                "dueDate": 1664744400000
            },
            "name": "Second Task",
            "type": "task",
            "namespace": {
                "functionName": "move_to_task",
                "projectName": "DataloopTasks",
                "serviceName": "pipeline-utils",
                "moduleName": "default_module",
                "packageName": "pipeline-utils"
            },
            "projectId": "f8a4b8ce-5ff3-4386-84dc-1bda3a5bc92a"
        }
    ],
    "connections": [
        {
            "src": {
                "nodeId": "021f90cf-65f8-4f61-a1a2-4775e3bff685",
                "portId": "572b01df-e336-4f91-b4e3-458d1e79f532"
            },
            "tgt": {
                "nodeId": "4a8bb1f9-7eb5-484a-8603-773d097f222b",
                "portId": "0a6b4481-efee-4cfa-b0cd-ffd42312a49f"
            },
            "condition": "{}"
        },
        {
            "src": {
                "nodeId": "039c747d-6ec3-4fbb-8090-6134ecc78ae6",
                "portId": "a6a3115e-7678-4f6a-b39b-2dd9f54d554f"
            },
            "tgt": {
                "nodeId": "0d811e02-aeea-475e-9514-9b497e215cab",
                "portId": "f7032c2a-f568-4971-ab7b-36c89a5d6e00"
            },
            "condition": "{}"
        },
        {
            "src": {
                "nodeId": "4a8bb1f9-7eb5-484a-8603-773d097f222b",
                "portId": "ee8bbdf2-0e33-4688-af5c-800d88c583d0"
            },
            "tgt": {
                "nodeId": "039c747d-6ec3-4fbb-8090-6134ecc78ae6",
                "portId": "0b357d4b-7e60-47a2-922e-7a22a4d7d6fc"
            },
            "condition": "{}",
            "action": "completed"
        },
        {
            "src": {
                "nodeId": "4a8bb1f9-7eb5-484a-8603-773d097f222b",
                "portId": "c7bdac4e-0a3c-4bf0-9e45-311e23b3dd5a"
            },
            "tgt": {
                "nodeId": "488d660b-9c81-4f12-ad38-7a57bcd3346c",
                "portId": "5a389b74-077f-4cde-a702-11775398bdb1"
            },
            "condition": "{}",
            "action": "completed"
        },
        {
            "src": {
                "nodeId": "4a8bb1f9-7eb5-484a-8603-773d097f222b",
                "portId": "fc09ca5d-9a13-438b-993a-5518dc67b045"
            },
            "tgt": {
                "nodeId": "967edc32-1eb3-4cfb-b127-8c3be9005726",
                "portId": "82dd52bc-7bc4-4baa-8f2c-8654022625e5"
            },
            "condition": "{}",
            "action": "done"
        }
    ],
    "startNodes": [
        {
            "nodeId": "021f90cf-65f8-4f61-a1a2-4775e3bff685",
            "type": "root",
            "trigger": {
                "type": "Event",
                "spec": {
                    "actions": [
                        "Created"
                    ],
                    "resource": "Item",
                    "executionMode": "Once",
                    "filter": {}
                }
            },
            "id": "cc0d7b84-1339-429a-8fcf-c1ef28c8aae5"
        }
    ]
}


def generate_pipeline_json(project: dl.Project, dataloop_project_id: str, dataset: dl.Dataset, service: dl.Service):
    pipeline = copy.deepcopy(pipeline_json)
    recipe = dataset.recipes.list()[0]
    pipeline['name'] = 'test-pipe-resume-{}'.format(random.randrange(10000, 100000))

    for node in pipeline['nodes']:
        node['projectId'] = project.id

    task_nodes = [node for node in pipeline['nodes'] if node['type'] == 'task']
    for node in task_nodes:
        node['projectId'] = dataloop_project_id
        node['metadata']["recipeTitle"] = recipe.title
        node['metadata']["recipeId"] = recipe.id
        node['metadata']["datasetId"] = dataset.id
        node['metadata']["taskOwner"] = dataset.creator
        node['metadata']["workload"] = [
            {
                "assigneeId": dataset.creator,
                "load": 100
            }
        ]

    faas_node = [node for node in pipeline['nodes'] if node['type'] == 'function'][0]
    module = [m for m in service.package.modules if m.name == service.module_name][0]
    func = module.functions[0]
    faas_node['namespace'] = {
        "functionName": func.name,
        "projectName": project.name,
        "serviceName": service.name,
        "moduleName": service.module_name,
        "packageName": service.package.name
    }

    return pipeline


@behave.given(u'I have a resumable pipeline')
def step_impl(context):
    pipeline_utils_faas = dl.services.get(service_name='pipeline-utils')
    pipeline_payload = generate_pipeline_json(
        project=context.project,
        dataloop_project_id=pipeline_utils_faas.project_id,
        dataset=context.dataset,
        service=context.service,
    )
    context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_payload)
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.given(u'Faas node service is paused')
def step_impl(context):
    context.service.pause()
    context.service = dl.services.get(service_id=context.service.id)


@behave.when(u'Faas node service is resumed')
def step_impl(context):
    context.service.resume()
    context.service = dl.services.get(service_id=context.service.id)


def get_filters(context, for_cycle=True):
    next_nodes = [
        n for n in context.pipeline.nodes if
        n.node_type == 'function' or n.name in [
            'Task Completed',
            'Assignment Completed'
        ]
    ]
    filters = dl.Filters(resource=dl.FiltersResource.EXECUTION)
    filters.add('pipeline.id', context.pipeline.id)
    if for_cycle:
        cycles_page = context.pipeline.pipeline_executions.list()
        cycle = cycles_page.items[0]
        assert cycles_page.items_count == 1
        filters.add('pipeline.executionId', cycle.id)
    filters.add(
        field='pipeline.nodeId',
        values=[n.node_id for n in next_nodes],
        operator=dl.FiltersOperations.IN
    )
    return filters


@behave.then(u'Next nodes should be executed')
def step_impl(context):
    interval = 3
    max_attempts = 15
    attempt = 0
    success = False
    filters = get_filters(context=context, for_cycle=False)

    while not success and attempt < max_attempts:
        executions_page = context.project.executions.list(filters=filters)
        success = executions_page.items_count == 3
        if success:
            break
        time.sleep(interval)
        attempt = attempt + 1

    assert success


@behave.then(u'Next nodes should not be executed')
def step_impl(context):
    filters = get_filters(context=context)
    executions_page = context.project.executions.list(filters=filters)
    assert executions_page.items_count == 0


@behave.given(u'Faas node execution is in queue')
def step_impl(context):
    executions = context.service.executions.list()
    assert executions.items_count == 1
    execution = executions.items[0]
    assert execution.latest_status['status'] == 'created'


@behave.when(u'Faas node service has completed')
def step_impl(context):
    executions = context.service.executions.list()
    assert executions.items_count == 1
    execution = executions.items[0]
    interval = 3
    max_attempts = 15
    attempt = 0
    while execution.latest_status['status'] != 'success' and attempt < max_attempts:
        time.sleep(interval)
        attempt = attempt + 1
        executions = context.service.executions.list()
        assert executions.items_count == 1
        execution = executions.items[0]

    assert execution.latest_status['status'] == 'success'


@behave.when(u'I complete item in task')
def step_impl(context):
    context.item.update_status(status=context.dl.ItemStatus.COMPLETED)
    interval = 1
    max_attempts = 10
    ready = False
    for _ in range(max_attempts):
        item = dl.items.get(item_id=context.item.id)
        task_refs = [ref for ref in item.system.get('refs') if ref['type'] == 'task']
        assert len(task_refs) == 1
        task_ref = task_refs[0]
        if task_ref.get('metadata', {}).get('status', None) == context.dl.ItemStatus.COMPLETED:
            ready = True
            break
        time.sleep(interval)

    assert ready
    time.sleep(5)  # allow extra time for events to get handled


@behave.given(u'Item reached task node')
def step_impl(context):
    interval = 3
    max_attempts = 15
    attempt = 0
    ready = False
    item = None
    while not ready and attempt < max_attempts:
        cycles_page = context.pipeline.pipeline_executions.list()
        if cycles_page.items_count == 1:
            cycle = cycles_page.items[0]
            filters = dl.Filters(resource=dl.FiltersResource.EXECUTION)
            filters.add('pipeline.id', context.pipeline.id)
            filters.add('pipeline.executionId', cycle.id)
            executions_page = context.project.executions.list(filters=filters)
            task_executions = [e for e in executions_page.items if e.function_name == 'move_to_task']
            if len(task_executions) == 1:
                task_execution = task_executions[0]
                if task_execution.latest_status['status'] == 'success':
                    item = dl.items.get(**task_execution.input['item'])
                    ready = len(item.system.get('refs', list())) == 2
                    break
        time.sleep(interval)
        attempt = attempt + 1
    assert ready
    context.item = item


@behave.then(u'Item proceeded to next node')
def step_impl(context):
    faas_node = [n for n in context.pipeline.nodes if n.node_type == 'function'][0]
    connection: dl.PipelineConnection = [
        con for con in context.pipeline.connections if con.source.node_id == faas_node.node_id
    ][0]
    next_node = [n for n in context.pipeline.nodes if n.node_type == 'task' and n.node_id == connection.target.node_id][0]
    interval = 3
    max_attempts = 15
    attempt = 0
    success = False
    while not success and attempt < max_attempts:
        filters = context.dl.Filters(
            resource=context.dl.FiltersResource.PIPELINE_EXECUTION,
            field='status',
            values='in-progress'
        )
        cycles_page = context.pipeline.pipeline_executions.list(filters=filters)
        if cycles_page.items_count == 1:
            cycle = cycles_page.items[0]
            filters = dl.Filters(resource=dl.FiltersResource.EXECUTION)
            filters.add('pipeline.id', context.pipeline.id)
            filters.add('pipeline.executionId', cycle.id)
            filters.add('pipeline.nodeId', next_node.node_id)
            executions_page = context.project.executions.list(filters=filters)
            success = executions_page.items_count == 1
            if success:
                break
        time.sleep(interval)
        attempt = attempt + 1
    assert success


@behave.when(u'I resume pipeline with resume option "{resume_option}"')
def step_impl(context, resume_option):
    context.pipeline.install(resume_option=resume_option)
