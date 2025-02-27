import random
import string
import time

import behave

import dtlpy as dl


@behave.when(u'I add a code node to the pipeline')
def step_impl(context):
    def run(item, string):
        item.metadata['user'] = {'userInput': string}
        item.update()
        return item

    context.new_node = dl.CodeNode(
        name='codeNode',
        position=(4, 4),
        project_id=context.project.id,
        method=run,
        project_name=context.project.name
    )

    context.pipeline.nodes.add(node=context.new_node)
    context.pipeline.update()


@behave.when(u'I add a predict node to the pipeline')
def step_impl(context):
    context.new_node = dl.entities.pipeline.PipelineNode.from_json({
        "id": "d4de0a46-7597-43bb-a80a-a77cb41ab62d",
        "inputs": [
            {
                "portId": "1dec3c79-680d-4ac7-b380-f51f9e578de6",
                "nodeId": "1dec3c79-680d-4ac7-b380-f51f9e578de6",
                "type": "Item",
                "name": "item",
                "displayName": "item",
                "io": "input"
            }
        ],
        "outputs": [
            {
                "portId": "5285f12a-ddbe-4e64-b8dd-acf1c05626a7",
                "nodeId": "5285f12a-ddbe-4e64-b8dd-acf1c05626a7",
                "type": "Item",
                "name": "item",
                "displayName": "item",
                "io": "output"
            },
            {
                "portId": "bc16fe31-8e42-47bc-912d-13e6b135f98c",
                "nodeId": "bc16fe31-8e42-47bc-912d-13e6b135f98c",
                "type": "Annotation[]",
                "name": "annotations",
                "displayName": "annotations",
                "io": "output"
            }
        ],
        "metadata": {
            "position": {
                "x": 1490,
                "y": 640,
                "z": 0
            },
            "modelName": context.model.name,
            "modelId": context.model.id,
            "serviceConfig": {

            }
        },
        "name": context.model.name,
        "type": "ml",
        "namespace": {
            "functionName": "predict",
            "projectName": context.project.name,
            "serviceName": "model-mgmt-app-predict",
            "moduleName": context.model.module_name,
            "packageName": "model-mgmt-app"
        },
        "projectId": context.project.id
    })

    context.pipeline.nodes.add(context.new_node)
    context.pipeline.update()


@behave.when(u'i update runnerImage "{image}" to pipeline node with type "{node_type}"')
def step_impl(context, image, node_type):
    context.pipeline = context.project.pipelines.get(pipeline_id=context.pipeline.id)
    for node in context.pipeline.nodes:
        if node.node_type == node_type:
            if 'serviceConfig' not in node.metadata:
                node.metadata['serviceConfig'] = {}
            if 'runtime' not in node.metadata['serviceConfig']:
                node.metadata['serviceConfig']['runtime'] = {}
            node.metadata['serviceConfig']['runtime']['runnerImage'] = image
            context.pipeline = context.pipeline.update()
            break

@behave.when(u'i get the service for the pipeline node with type "{node_type}"')
def step_impl(context, node_type):
    for node in context.pipeline.nodes:
        if node.node_type == node_type:
            context.service = dl.services.get(service_name=node.namespace.service_name)
            break

@behave.when(u'I execute the pipeline batch items')
def step_impl(context):
    context.command = context.pipeline.execute_batch(
        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
        filters=dl.Filters(field='dir', values='/test', context={'datasets': [context.dataset.id]}))


@behave.when(u'I get the pipeline service')
def step_impl(context):
    service_name = context.pipeline.nodes[0].namespace.service_name
    context.service = dl.services.get(service_name=service_name)

@behave.when(u'I execute the full dataset items on function "{func_name}"')
def step_impl(context, func_name):
    context.command = context.service.execute_batch(
        filters=dl.Filters(context={'datasets': [context.dataset.id]}), function_name=func_name)

@behave.when(u'I execute the service batch items')
def step_impl(context):
    context.command = context.service.execute_batch(
        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
        filters=dl.Filters(field='dir', values='/test', context={'datasets': [context.dataset.id]}))


@behave.then(u'pipeline execution are success in "{items_count}" items')
def step_impl(context, items_count):
    assert context.command.status == dl.ExecutionStatus.SUCCESS
    assert len(context.command.spec['inputs']) == eval(items_count)
    assert context.pipeline.pipeline_executions.list().items_count == eval(items_count)


@behave.then(u'service execution are success in "{items_count}" items')
def step_impl(context, items_count):
    assert context.command.status == dl.ExecutionStatus.SUCCESS
    assert len(context.command.spec['inputs']) == eval(items_count)
    assert context.service.executions.list().items_count == eval(items_count)


@behave.given(u'I install a pipeline with 2 dataset nodes')
def step_impl(context):
    pipeline_json = {
        "nodes": [
            {
                "id": "64d7bf6f-e42e-4693-9319-a389cea84680",
                "inputs": [
                    {
                        "portId": "286ebf65-7c96-4a25-826a-2901c978013b",
                        "nodeId": "286ebf65-7c96-4a25-826a-2901c978013b",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "a2916fdb-199f-420d-b9c7-c81cbbdff7fb",
                        "nodeId": "a2916fdb-199f-420d-b9c7-c81cbbdff7fb",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10217,
                        "y": 10127,
                        "z": 0
                    },
                    "datasetId": context.dataset.id,
                    "componentGroupName": "data",
                    "repeatable": True
                },
                "name": context.dataset.name,
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
                "id": "d65c4651-28aa-4fed-a5f4-71e4fcfd2e15",
                "inputs": [
                    {
                        "portId": "5aed83a8-d3b6-45ed-b323-697379d0fe2e",
                        "nodeId": "5aed83a8-d3b6-45ed-b323-697379d0fe2e",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "00e0fe41-c57a-45a2-939a-6650f9e19868",
                        "nodeId": "00e0fe41-c57a-45a2-939a-6650f9e19868",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10644,
                        "y": 10176,
                        "z": 0
                    },
                    "datasetId": context.dataset.id,
                    "componentGroupName": "data",
                    "repeatable": True
                },
                "name": context.dataset.name,
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
                    "nodeId": "64d7bf6f-e42e-4693-9319-a389cea84680",
                    "portId": "a2916fdb-199f-420d-b9c7-c81cbbdff7fb"
                },
                "tgt": {
                    "nodeId": "d65c4651-28aa-4fed-a5f4-71e4fcfd2e15",
                    "portId": "5aed83a8-d3b6-45ed-b323-697379d0fe2e"
                },
                "condition": "{}"
            }
        ],
        "startNodes": [
            {
                "nodeId": "64d7bf6f-e42e-4693-9319-a389cea84680",
                "type": "root",
                "id": "90ae8a0d-287b-4e19-821d-e4b03edaf5a4"
            }
        ]
    }
    context.pipeline = context.project.pipelines.create(
        pipeline_json=pipeline_json,
        name="test-execute-specific-node-{}".format(
            ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'
        )
    )
    context.pipeline.install()


@behave.when(u'I execute the second node which is not the root node')
def step_impl(context):
    context.root_node_id = context.pipeline.start_nodes[0]['nodeId']
    context.execution_node_id = [n for n in context.pipeline.nodes if n.node_id != context.root_node_id][0].node_id
    context.cycle = context.pipeline.execute(node_id=context.execution_node_id,
                                             execution_input={'item': context.item.id})


@behave.then(u'Then pipeline should start from the requested node')
def step_impl(context):
    timeout = 60 * 1
    start_time = time.time()
    success = False
    while time.time() - start_time < timeout:
        time.sleep(1)
        cycle = context.pipeline.pipeline_executions.get(pipeline_execution_id=context.cycle.id)
        if cycle.status == 'success':
            root_node = [n for n in cycle.nodes if n.node_id == context.root_node_id][0]
            execution_node = [n for n in cycle.nodes if n.node_id == context.execution_node_id][0]
            success = root_node.status == 'pending'
            success = success and execution_node.status == 'success'
            if success:
                break

    assert success, 'Pipeline did not start from the requested node'
