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

    def run(item):
        item.metadata['user'] = {'Hello': 'World'}
        item.update()
        return item

    code_node = dl.CodeNode(
        name='My Function',
        position=(3, 3),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    context.pipeline.nodes.add(node=function_node).connect(node=task_node) \
        .connect(node=code_node)
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

    def run(item):
        item.metadata['user'] = {'Hello': 'World'}
        item.update()
        return item

    code_node = dl.CodeNode(
        name='My Function',
        position=(3, 3),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    context.pipeline.nodes.add(node=function_node).connect(node=task_node) \
        .connect(node=code_node)
    context.pipeline.update()
    context.pipeline.triggers.create(actions=dl.TriggerAction.CREATED, pipeline_node_id=function_node.node_id,
                                     project_id=context.project.id)
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I update pipeline trigger action')
def step_impl(context):
    context.trigger = context.pipeline.triggers.list()[0][0]
    context.trigger.actions = [dl.TriggerAction.UPDATED]
    context.trigger.update()


@behave.then(u'valid trigger updated')
def step_impl(context):
    trigger = context.pipeline.triggers.get(trigger_id=context.trigger.id)
    original_trigger_json = context.trigger.to_json()
    updated_trigger_json = trigger.to_json()
    original_trigger_json.get('spec', {}).pop('actions', None)
    assert updated_trigger_json.get('spec', {}).pop('actions', None) == [dl.TriggerAction.UPDATED]
    assert updated_trigger_json.get('spec') == original_trigger_json.get('spec')


@behave.when(u'I add trigger to the node and check installed with param keep_triggers_active equal to "{keep_triggers_active}"')
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

    pipeline_json['nodes'][2]['namespace']['projectName'] = context.project.name

    context.pipeline = context.project.pipelines.create(pipeline_json=pipeline_json)
    context.pipeline.install()
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@behave.when(u'I upload item in "{item_path}" to pipe dataset')
def step_impl(context, item_path):
    time.sleep(30)
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)


@behave.then(u'verify pipeline flow result')
def step_impl(context):
    time.sleep(15)
    context.item = context.dataset.items.get(item_id=context.item.id)
    assert context.item.metadata['system'].get('fromPipe', False)
    time.sleep(20)
    context.item = context.dataset.items.get(item_id=context.item.id)
    ass_id = None
    for ref in context.item.metadata['system']['refs']:
        if ref['type'] == 'assignment':
            ass_id = ref['id']
    context.item.update_status(status='complete', assignment_id=ass_id, clear=False)
    current_num_of_tries = 0
    flag = False
    while flag is False and current_num_of_tries < 6:
        time.sleep(10)
        context.item = context.dataset.items.get(item_id=context.item.id)
        try:
            if context.item.metadata['user'] == {'Hello': 'World'}:
                flag = True
        except:
            current_num_of_tries += 1

    assert flag


@behave.when(u'I update the pipeline nodes')
def step_impl(context):
    context.pipeline.pause()
    context.pipeline.nodes.remove("My Function")
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

    context.dataset_finish = context.project.datasets.create(dataset_name='dataset-' + current_time + "-finish")
    context.pipeline = context.project.pipelines.create(pipeline_name='sdk-pipeline-sanity')

    task_node_1 = dl.TaskNode(
        name='My Task-fix-label' + current_time,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner="nirrozmarin@dataloop.ai",
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
        task_owner="nirrozmarin@dataloop.ai",
        workload=[dl.WorkloadUnit(assignee_id="oa-test-1@dataloop.ai", load=100)],
        position=(1, 2),
        project_id=context.project_id,
        dataset_id=context.dataset.id
    )

    task_node_3 = dl.TaskNode(
        name='My QA Task' + current_time,
        recipe_id=context.recipe.id,
        recipe_title=context.recipe.title,
        task_owner="nirrozmarin@dataloop.ai",
        workload=[dl.WorkloadUnit(assignee_id="nirrozmarin@dataloop.ai", load=100)],
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
        name='sdk-pipeline-sanity-{}'.format(random.randrange(1000, 10000)))

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


@behave.then(u'I expect that pipeline execution has "{execution_number}" success executions')
def step_impl(context, execution_number):
    time.sleep(2)
    assert context.pipeline.pipeline_executions.list().items_count != 0, "Pipeline not executed found 0 executions"
    context.pipeline = context.project.pipelines.get(context.pipeline.name)

    num_try = 10
    interval = 10
    validate = 0
    executed = False

    for i in range(num_try):
        time.sleep(interval)
        execution_list = context.pipeline.pipeline_executions.list()[0][0].executions
        execution_count = 0
        for ex in execution_list.values():
            execution_count = execution_count + len(ex)
        if execution_count == int(execution_number):
            validate += 1
            if validate == 2:
                executed = True
                break

    assert executed, "TEST FAILED: Pipeline has {} executions instead of {}".format(execution_count, execution_number)
    return executed


@behave.when(u'I create a pipeline dataset, task "{type}" and code nodes - repeatable "{flag}"')
def step_impl(context, type, flag):
    flag = eval(flag)

    t = time.localtime()
    current_time = time.strftime("%H-%M-%S", t)
    pipeline_name = 'pipeline-sdk-{}'.format(current_time)

    context.pipeline = context.project.pipelines.create(name=pipeline_name)

    dataset_node = dl.DatasetNode(
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
        task_owner="nirrozmarin@dataloop.ai",
        workload=[dl.WorkloadUnit(assignee_id="oa-test-1@dataloop.ai", load=100)],
        position=(2, 2),
        task_type=type,
        project_id=context.project.id,
        dataset_id=context.dataset.id,
        repeatable=flag
    )

    function_node = dl.FunctionNode(
        name='automate',
        position=(3, 3),
        service=dl.services.get(service_id=context.service.id),
        function_name='automate'
    )

    context.pipeline.nodes.add(dataset_node).connect(node=task_node).connect(node=function_node,
                                                                             source_port=task_node.outputs[0])
    dataset_node.add_trigger()

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
