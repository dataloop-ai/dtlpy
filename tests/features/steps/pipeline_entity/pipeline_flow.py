import os
import time

import dtlpy as dl
import behave
import json


@behave.when(u'I create a package and service to pipeline')
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

    project = dl.projects.get(project_name=context.project.name)
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
    payload = {"operation": "create", "status": "complete"}
    dl.client_api.gen_request(
        req_type='post',
        path='/assignments/{}/items/{}/status'.format(ass_id, context.item.id),
        json_req=payload
    )
    time.sleep(30)
    context.item = context.dataset.items.get(item_id=context.item.id)
    assert context.item.metadata['user'] == {'Hello': 'World'}


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
        workload=[dl.WorkloadUnit(assignee_id=dl.info()['user_email'], load=50), dl.WorkloadUnit(assignee_id="annotator1@dataloop.ai", load=50)],
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

    context.pipeline.nodes.add(task_node_1).connect(node=task_node_2, source_port=task_node_1.outputs[2], target_port=task_node_2.inputs[0]).connect(node=task_node_3,
                                                                                                                                                     source_port=task_node_2.outputs[0]) \
        .connect(node=code_node, source_port=task_node_3.outputs[0]).connect(node=dataset_node).connect(node=function_node)

    filters = dl.Filters(field='datasetId', values=context.dataset.id)
    task_node_1.add_trigger(filters=filters)

    context.pipeline.update()
    context.pipeline.install()
