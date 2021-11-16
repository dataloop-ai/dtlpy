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
    time.sleep(25)
    context.item = context.dataset.items.get(item_id=context.item.id)
    assert context.item.metadata['user'] == {'Hello': 'World'}
