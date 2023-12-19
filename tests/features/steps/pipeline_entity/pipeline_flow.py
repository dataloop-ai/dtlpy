import os
import time
import uuid
import random

import dtlpy as dl
import behave
import json


@behave.when(u'I create a package and service to pipeline')
@behave.given(u'I create a package and service to pipeline')
def step_impl(context):
    module = dl.PackageModule(
        entry_point='main.py',
        class_name='ServiceRunner',
        functions=[
            dl.PackageFunction(
                name='automate',
                inputs=[
                    dl.FunctionIO(type="Item", name="item")
                ],
                outputs=[
                    dl.FunctionIO(type="Item", name="item")
                ],
                description=''
            )
        ])

    project = dl.projects.get(project_id=context.project.id)
    context.package = project.packages.push(
        package_name='test-pipeline',
        modules=[module],
        src_path=os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "pipeline_flow")
    )

    context.service = context.package.services.deploy(service_name=context.package.name,
                                                      package=context.package,
                                                      runtime={"gpu": False, "numReplicas": 1, 'concurrency': 1,
                                                               'autoscaler': {
                                                                   'type': dl.KubernetesAutuscalerType.RABBITMQ,
                                                                   'minReplicas': 1,
                                                                   'maxReplicas': 5,
                                                                   'queueLength': 10}}
                                                      )
    context.to_delete_services_ids.append(context.service.id)
    time.sleep(10)


@behave.when(u'I create a pipeline from sdk')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='sdk-pipeline-test', project_id=context.project.id)

    function_node = dl.FunctionNode(
        name='automate',
        position=(1, 1),
        service=dl.services.get(service_id=context.service.id),
        function_name='automate'
    )

    task_node = dl.TaskNode(
        name='My Task',
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(2, 2),
        project_id=context.project.id,
        dataset_id=context.dataset.id,
    )

    dataset_node = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(3, 3)
    )

    context.pipeline.nodes.add(node=function_node).connect(node=task_node).connect(node=dataset_node)
    function_node.add_trigger()
    context.pipeline.update()
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I add a node and connect it to the start node')
def step_impl(context):
    context.pipeline.pause()

    def run(item):
        item.metadata['user'] = {'Hello': 'World'}
        item.update()
        return item

    context.new_node = dl.CodeNode(
        name='My Function',
        position=(4, 4),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    context.pipeline.nodes.add(node=context.new_node).connect(node=context.pipeline.nodes[0])
    context.pipeline.update()


@behave.then(u'New node is the start node')
def step_impl(context):
    assert context.new_node.is_root()


@behave.when(u'I create a pipeline from sdk with pipeline trigger')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='sdk-pipeline-test', project_id=context.project.id)

    dataset_node_1 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(1, 1)
    )

    dataset_node_2 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 2)
    )

    context.pipeline.nodes.add(node=dataset_node_1).connect(node=dataset_node_2)
    context.pipeline.update()
    context.pipeline.triggers.create(actions=dl.TriggerAction.CREATED, pipeline_node_id=dataset_node_1.node_id,
                                     project_id=context.project.id)
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I update pipeline trigger action')
def step_impl(context):
    context.trigger = context.pipeline.triggers.list()[0][0]
    context.trigger.actions = [dl.TriggerAction.UPDATED]
    context.trigger = context.trigger.update()


@behave.then(u'valid trigger updated')
def step_impl(context):
    trigger = context.pipeline.triggers.get(trigger_id=context.trigger.id)
    original_trigger_json = context.trigger.to_json()
    updated_trigger_json = trigger.to_json()
    original_trigger_json.get('spec', {}).pop('actions', None)
    assert updated_trigger_json.get('spec', {}).pop('actions', None) == [dl.TriggerAction.UPDATED]
    assert updated_trigger_json.get('spec') == original_trigger_json.get('spec')


@behave.when(
    u'I add trigger to the node and check installed with param keep_triggers_active equal to "{keep_triggers_active}"')
def step_impl(context, keep_triggers_active: str):
    keep_triggers_active = eval(keep_triggers_active)
    context.pipeline.pause(keep_triggers_active=keep_triggers_active)
    node_id = context.pipeline.nodes[1].node_id
    context.pipeline.triggers.create(pipeline_node_id=node_id)
    triggers = context.pipeline.triggers.list().items
    for trigger in triggers:
        assert trigger.active == keep_triggers_active
    context.pipeline.install()
    triggers = context.pipeline.triggers.list().items
    assert len(triggers) == 2
    for trigger in triggers:
        assert trigger.active


@behave.when(u'I create a pipeline from json')
def step_impl(context):
    pipeline_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "pipeline_flow/pipeline_flow.json")

    with open(pipeline_path, 'r') as f:
        pipeline_json = json.load(f)

    pipeline_json['projectId'] = context.project.id

    pipeline_json['nodes'][0]['namespace']['serviceName'] = context.service.name
    pipeline_json['nodes'][0]['namespace']['packageName'] = context.package.name
    pipeline_json['nodes'][0]['namespace']['projectName'] = context.project.name
    pipeline_json['nodes'][0]['projectId'] = context.project.id

    pipeline_json['nodes'][1]['metadata']['recipeTitle'] = context.recipe.title
    pipeline_json['nodes'][1]['metadata']['recipeId'] = context.recipe.id
    pipeline_json['nodes'][1]['metadata']['datasetId'] = context.dataset.id
    pipeline_json['nodes'][1]['metadata']["workload"] = [
        {
            "assigneeId": dl.info()['user_email'],
            "load": 100
        }
    ]

    pipeline_json['nodes'][2]['namespace']['projectName'] = context.project.name

    context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_json, project_id=context.project.id)
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.given(u'I have a custom "{name}" pipeline from json')
def step_impl(context, name: str):
    pipeline_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "pipeline_flow/{}.json".format(name))

    with open(pipeline_path, 'r') as f:
        pipeline_json = json.load(f)

    pipeline_json['projectId'] = context.project.id

    for node in pipeline_json['nodes']:
        if node['type'] in ['code', 'function']:
            node['namespace']['projectName'] = context.project.name
            node['projectId'] = context.project.id
        elif node['type'] == 'task':
            node['metadata']['recipeTitle'] = context.recipe.title
            node['metadata']['recipeId'] = context.recipe.id
            node['metadata']['datasetId'] = context.dataset.id
            node['metadata']["taskOwner"] = dl.info()['user_email']
            node['metadata']["workload"] = [
                {
                    "assigneeId": dl.info()['user_email'],
                    "load": 100
                }
            ]

    context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_json, project_id=context.project.id)
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)

    tasks = context.pipeline.project.tasks.list()

    if len(tasks) == 1:
        context.task = tasks[0]
    elif len(tasks) > 1:
        context.tasks = tasks


@behave.when(u'I upload item in "{item_path}" to pipe dataset')
def step_impl(context, item_path):
    time.sleep(5)
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.then(u'verify pipeline flow result')
def step_impl(context):
    interval = 10
    num_tries = 30
    fromPipe = False
    for i in range(num_tries):
        time.sleep(interval)
        context.item = context.dataset.items.get(item_id=context.item.id)
        if context.item.metadata['system'].get('fromPipe', False):
            fromPipe = True
            break
    assert fromPipe, f"TEST FAILED: item.metadata['system'] missing fromPipe: True, after {round(num_tries * interval / 60, 1)} minutes"

    time.sleep(20)
    context.item = context.dataset.items.get(item_id=context.item.id)
    ass_id = None
    for ref in context.item.metadata['system']['refs']:
        if ref['type'] == 'assignment':
            ass_id = ref['id']
    context.item.update_status(status='complete', assignment_id=ass_id, clear=False)


@behave.when(u'I remove node by the name "{node_name}" from pipeline')
def step_impl(context, node_name):
    context.pipeline.pause()
    context.pipeline = context.pipeline.pipelines.get(context.pipeline.name)
    context.pipeline.nodes.remove(node_name)
    context.pipeline.update()


@behave.when(u'check pipeline nodes')
def step_impl(context):
    assert len(context.pipeline.nodes) == 2
    assert len(context.pipeline.connections) == 1


@behave.then(u'verify pipeline sanity result')
def step_impl(context):
    assert context.dataset_finish.items.list().item_count != 0, "No items in dataset finished - Pipeline failed"

    for task in context.project.tasks.list():
        task.item_status


@behave.when(u'I create a pipeline from pipeline-sanity')
def step_impl(context):
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)

    context.dataset_finish = context.project.datasets.create(dataset_name='dataset-' + current_time + "-finish", index_driver=context.index_driver_var)
    context.pipeline = context.project.pipelines.create(pipeline_name='sdk-pipeline-sanity', project_id=context.project.id)

    task_node_1 = dl.TaskNode(
        name='My Task-fix-label' + current_time,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=50),
                  dl.WorkloadUnit(assignee_id="annotator1@dataloop.ai", load=50)],
        position=(1, 1),
        project_id=context.project_id,
        dataset_id=context.dataset.id,
        actions=('complete', 'discard', 'fix-label')
    )

    task_node_2 = dl.TaskNode(
        name='My Task-completed' + current_time,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(1, 2),
        project_id=context.project_id,
        dataset_id=context.dataset.id
    )

    task_node_3 = dl.TaskNode(
        name='My QA Task' + current_time,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(1, 3),
        project_id=context.project_id,
        dataset_id=context.dataset.id,
        task_type='qa'
    )

    def run(item: dl.Item):
        item.metadata['user'] = {'Hello': 'World'}
        item.update()
        return item

    code_node = dl.CodeNode(
        name='My Function',
        position=(2, 2),
        project_id=context.project_id,
        method=run,
        project_name=context.project.name
    )

    dataset_node = dl.DatasetNode(
        name=context.dataset_finish.name,
        project_id=context.project_id,
        dataset_id=context.dataset_finish.id,
        position=(3, 3)
    )

    function_node = dl.FunctionNode(
        name='automate',
        position=(4, 4),
        service=dl.services.get(service_id=context.service.id),
        function_name='automate'
    )

    context.pipeline.nodes.add(task_node_1).connect(node=task_node_2, source_port=task_node_1.outputs[2],
                                                    target_port=task_node_2.inputs[0]).connect(node=task_node_3,
                                                                                               source_port=
                                                                                               task_node_2.outputs[0]) \
        .connect(node=code_node, source_port=task_node_3.outputs[0]).connect(node=dataset_node).connect(
        node=function_node)

    filters = dl.Filters(field='datasetId', values=context.dataset.id)
    task_node_1.add_trigger(filters=filters)

    context.pipeline.update()
    context.pipeline.install()


@behave.when(u'I create a pipeline with dataset resources')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(
        name='sdk-pipeline-sanity-{}'.format(random.randrange(1000, 10000)), project_id=context.project.id)

    def run_1(item: dl.Item):
        dataset = item.dataset
        return dataset

    code_node_1 = dl.CodeNode(
        name='My Function',
        position=(0, 0),
        project_id=context.project.id,
        method=run_1,
        project_name=context.project.name,
        outputs=[dl.PipelineNodeIO(port_id=str(uuid.uuid4()),
                                   input_type=dl.PackageInputType.DATASET,
                                   name='dataset',
                                   display_name='dataset')]
    )

    def run_2(dataset: dl.Dataset):
        for page in dataset.items.list():
            for item in page:
                break
        return item

    code_node_2 = dl.CodeNode(
        name='My Function',
        position=(2, 0),
        project_id=context.project.id,
        method=run_2,
        project_name=context.project.name,
        inputs=[dl.PipelineNodeIO(port_id=str(uuid.uuid4()),
                                  input_type=context.dl.PackageInputType.DATASET,
                                  name='dataset',
                                  display_name='dataset')]
    )

    context.pipeline.nodes.add(code_node_1).connect(node=code_node_2, filters=context.filters)

    code_node_1.add_trigger()
    context.pipeline.update()
    context.pipeline.install()


@behave.when(u'I create a pipeline dataset, task "{type}" and dataset nodes - repeatable "{flag}"')
def step_impl(context, type, flag):
    flag = eval(flag)

    num = random.randrange(10000, 100000)
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    pipeline_name = f'pipeline-sdk-{num}'

    context.pipeline = context.project.pipelines.create(name=pipeline_name, project_id=context.project.id)

    dataset_node_1 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(1, 1)
    )

    task_name = 'My Task-completed' + current_time
    task_node = dl.TaskNode(
        name=task_name,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(2, 2),
        task_type=type,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        repeatable=flag
    )

    dataset_node_2 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(3, 3)
    )

    context.pipeline.nodes.add(dataset_node_1).connect(node=task_node).connect(node=dataset_node_2,
                                                                               source_port=task_node.outputs[0])
    dataset_node_1.add_trigger()

    context.pipeline.update()
    pipeline = context.project.pipelines.get(pipeline_name=pipeline_name)
    pipeline.install()

    time.sleep(5)
    try:
        context.task = context.project.tasks.get(task_name=task_name + " (" + pipeline_name + ")")
    except Exception as e:
        assert False, "Failed to get task with the name: {}\n{}".format(task_name + " (" + pipeline_name + ")", e)


@behave.when(u'I create a pipeline with task node and new recipe')
def step_impl(context):
    context.pipeline = context.project.pipelines.create(name='sdk-pipeline-test', project_id=context.project.id)

    task_node = dl.TaskNode(
        name='My Task',
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=100)],
        position=(2, 2),
        project_id=context.project.id,
        dataset_id=context.dataset.id,
    )

    context.pipeline.nodes.add(node=task_node)
    context.pipeline.update()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.given(u'a pipeline with same item enters task twice')
def step_impl(context):
    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    context.task_name = 'My Task-completed' + current_time

    context.task_node = dl.TaskNode(
        name=context.task_name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner=context.dl.info()['user_email'],
        workload=[dl.WorkloadUnit(assignee_id=context.dl.info()['user_email'], load=100)],
        position=(3, 5),
        task_type='annotation',
        priority=dl.entities.TaskPriority.LOW
    )

    context.dataset_node_1 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(1, 5)
    )

    context.dataset_node_2 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 3)
    )

    context.dataset_node_3 = dl.DatasetNode(
        name=context.dataset.name,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        position=(2, 7)
    )

    context.pipeline_name = 'pipeline-{}'.format(current_time)
    context.pipeline = context.project.pipelines.create(name='pipeline-sdk-test', project_id=context.project.id)
    context.dataset_node_1 = context.pipeline.nodes.add(context.dataset_node_1)
    context.dataset_node_1.connect(node=context.dataset_node_2, source_port=context.dataset_node_1.outputs[0],
                                   target_port=context.dataset_node_2.inputs[0])
    context.dataset_node_1.connect(node=context.dataset_node_3, source_port=context.dataset_node_1.outputs[0],
                                   target_port=context.dataset_node_3.inputs[0])
    context.dataset_node_2.connect(node=context.task_node, source_port=context.dataset_node_2.outputs[0],
                                   target_port=context.task_node.inputs[0])
    context.dataset_node_3.connect(node=context.task_node, source_port=context.dataset_node_3.outputs[0],
                                   target_port=context.task_node.inputs[0])
    context.pipeline.update()
    context.pipeline.install()
    context.task = context.project.tasks.list()[0]
    context.pipeline = context.dl.pipelines.get(pipeline_id=context.pipeline.id)
    is_installed = context.pipeline.status == 'Installed'
    assert is_installed, "Pipeline was not installed"


@behave.when(u'I execute pipeline on item')
def step_impl(context):
    context.pipeline: dl.Pipeline
    context.cycle = context.pipeline.execute(execution_input={'item': context.item.id})


@behave.when(u'I wait for item to enter task')
def step_impl(context):
    time.sleep(2)

    num_try = 10
    interval = 10
    entered = False

    for i in range(num_try):
        time.sleep(interval)
        context.item = context.dl.items.get(item_id=context.item.id)
        refs = context.item.metadata.get('system', {}).get('refs', [])
        if len(refs) > 0:
            entered = True
            break

    assert entered, f"TEST FAILED: Item was not move to task, after {round(num_try * interval / 60, 1)} minutes"


@behave.then(u'Cycle should be completed')
def step_impl(context):
    time.sleep(2)

    num_try = 10
    interval = 10
    completed = False

    for i in range(num_try):
        time.sleep(interval)
        pipeline: dl.Pipeline = context.pipeline
        context.cycle: dl.PipelineExecution = pipeline.pipeline_executions.list().items[0]
        if context.cycle.status == 'success':
            completed = True
            break

    assert completed, "TEST FAILED: cycle was not completed"


@behave.then(u'Context should have all required properties')
def step_impl(context):
    timeout = 60 * 10
    interval = 5
    start_time = time.time()
    execution = None
    success = False
    while time.time() - start_time < timeout:
        cycles = context.pipeline.pipeline_executions.list().items
        success = [False for i in cycles]
        for i in range(len(cycles)):
            if cycles[i].status == 'success':
                success[i] = True
        if all(success):
            success = True
            break
        time.sleep(interval)

    if success:
        services = context.project.services.list().all()
        for service in services:
            executions = service.executions.list()
            assert executions.items_count == 1
            execution = executions.items[0]
            assert execution is not None, "TEST FAILED: execution was not found"
            assert execution.output['taskName'] == context.task.name
            assert execution.output['pipelineName'] == context.pipeline.name
            assert execution.output['nodeName'] == [n for n in context.pipeline.nodes if n.namespace.service_name == service.name][0].name
            assert execution.output['assignmentName'] == context.task.assignments.list()[0].name
            assert execution.output['itemStatus'] == context.item_status
