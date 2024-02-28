from behave import given, when, then
import random
import string


def random_5_chars():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'


@given(u'a service')
def step_impl(context):
    def run(item):
        print('hello world')

    context.service = context.project.services.deploy(
        service_name='test-service-{}'.format(random_5_chars()),
        func=run,
    )
    context.package = context.service.package


@given(u'model is trained')
def step_impl(context):
    context.model.status = 'trained'
    context.model = context.model.update()
    assert context.model.status == 'trained'


@given(u'a dpk with custom node')
def step_impl(context):
    dpk_json = {
        "name": "test-dpk-with-custom-node-{}".format(
            ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))),
        "version": "0.0.21",
        "displayName": "Test",
        "codebase": {
            "type": "git",
            "gitUrl": "https://github.com/dataloop-ai-apps/data-split.git",
            "gitTag": "v0.0.21"
        },
        "scope": "project",
        "latest": True,
        "components": {
            "pipelineNodes": [
                {
                    "panel": "dataSplit",
                    "name": "dataSplit",
                    "invoke": {
                        "type": "function",
                        "namespace": "data-split.data_split.data_split"
                    },
                    "categories": [
                        "data"
                    ],
                    "scope": "project"
                }
            ],
            "modules": [
                {
                    "name": "data_split",
                    "entryPoint": "modules/data_split.py",
                    "className": "ServiceRunner",
                    "initInputs": [

                    ],
                    "functions": [
                        {
                            "name": "data_split",
                            "description": "The 'Data Split' node is a data processing tool that allows you to dynamically split your data into multiple groups at runtime. Whether you need to sample items for QA tasks or divide the items into multiple datasets, the Data Split node makes it easy.\n \n Simply define your groups, set their distribution, and tag each item with its assigned group using a metadata field. Use the Data Split node at any point in your pipeline to customize your data processing.",
                            "input": [
                                {
                                    "type": "Item",
                                    "name": "item"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Item",
                                    "name": "item"
                                }
                            ],
                            "displayIcon": "qa-sampling",
                            "displayName": "Data Split"
                        }
                    ]
                }
            ]
        }
    }
    dpk = context.dl.Dpk.from_json(_json=dpk_json)
    context.dpk = context.project.dpks.publish(dpk=dpk)


@given(u'an app')
def step_impl(context):
    context.app = context.project.apps.install(
        dpk=context.dpk,
        app_name='test-app-{}'.format(random_5_chars()),
    )


@given(u'pipeline with model, service, code and custom nodes')
def step_impl(context):
    pipeline_json = {
        "name": "test-pipeline-{}".format(random_5_chars()),
        "projectId": context.project.id,
        "nodes": [
            {
                "id": "5e01d6b5-34be-499c-b0d8-e4facddb02f9",
                "inputs": [
                    {
                        "portId": "fda6a964-1458-4214-bc8f-1bb2a844a745",
                        "nodeId": "fda6a964-1458-4214-bc8f-1bb2a844a745",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "59958af9-7592-4c86-a785-fd6bc5da6720",
                        "nodeId": "59958af9-7592-4c86-a785-fd6bc5da6720",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 65,
                        "y": 115,
                        "z": 0
                    },
                    "repeatable": True
                },
                "name": "FaaS Node",
                "type": "function",
                "namespace": {
                    "functionName": context.package.modules[0].functions[0].name,
                    "projectName": context.project.name,
                    "serviceName": context.service.name,
                    "moduleName": context.package.modules[0].name,
                    "packageName": context.package.name
                },
                "projectId": context.project.id,
            },
            {
                "id": "6062556d-b52b-4d2c-80cc-4cde0ad8c658",
                "inputs": [
                    {
                        "portId": "d9b23659-b30d-4106-9994-2fe0e86c0d1d",
                        "nodeId": "d9b23659-b30d-4106-9994-2fe0e86c0d1d",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "3cdb543b-0dec-4c9f-b856-296a78b2ae75",
                        "nodeId": "3cdb543b-0dec-4c9f-b856-296a78b2ae75",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 366,
                        "y": 179,
                        "z": 0
                    },
                    "codeApplicationName": "run",
                    "repeatable": True
                },
                "name": "code",
                "type": "code",
                "namespace": {
                    "functionName": "run",
                    "projectName": context.project.name,
                    "serviceName": "run",
                    "packageName": "run"
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
            },
            {
                "id": "43c05110-1741-4526-b78d-5bc548704825",
                "inputs": [
                    {
                        "portId": "f1f4c910-cd19-40a6-ba6c-1b91478175bc",
                        "nodeId": "f1f4c910-cd19-40a6-ba6c-1b91478175bc",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "1f7cd844-3785-4e0b-b533-7d4ce15c1642",
                        "nodeId": "1f7cd844-3785-4e0b-b533-7d4ce15c1642",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 674,
                        "y": 246,
                        "z": 0
                    },
                    "componentGroupName": "data",
                    "repeatable": True,
                    "pipelineNodeName": context.dpk.components.pipeline_nodes[0]['name'],
                },
                "name": "Data Split",
                "type": "custom",
                "namespace": {
                    "functionName": context.dpk.components.modules[0].functions[0].name,
                    "projectName": context.project.name,
                    "serviceName": "data-split",
                    "moduleName": context.dpk.components.modules[0].name,
                    "packageName": context.dpk.name
                },
                "projectId": context.project.id,
                "appName": context.app.name,
                "dpkName": context.dpk.name,
            },
            {
                "id": "c4d1230b-d5e1-4bdf-9b2a-0f98aaaa28d3",
                "inputs": [
                    {
                        "portId": "4cf7e27d-c4a4-4bde-b734-6e00b46cd63d",
                        "nodeId": "4cf7e27d-c4a4-4bde-b734-6e00b46cd63d",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "849e50a4-e771-4969-86fd-394847302e23",
                        "nodeId": "849e50a4-e771-4969-86fd-394847302e23",
                        "type": "Item",
                        "name": "item",
                        "displayName": "item",
                        "io": "output"
                    },
                    {
                        "portId": "50e3f7f6-c22f-43ad-aed0-ff283fee1636",
                        "nodeId": "50e3f7f6-c22f-43ad-aed0-ff283fee1636",
                        "type": "Annotation[]",
                        "name": "annotations",
                        "displayName": "annotations",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 968,
                        "y": 304,
                        "z": 0
                    },
                    "modelName": context.model.name,
                    "modelId": context.model.id,
                    "repeatable": True
                },
                "name": context.model.name,
                "type": "ml",
                "namespace": {
                    "functionName": "predict",
                    "projectName": context.project.name,
                    "serviceName": "m",
                    "moduleName": context.model.module_name,
                    "packageName": context.model.package.name
                },
                "projectId": context.project.id,
            }
        ],
        "connections": [
            {
                "src": {
                    "nodeId": "5e01d6b5-34be-499c-b0d8-e4facddb02f9",
                    "portId": "59958af9-7592-4c86-a785-fd6bc5da6720"
                },
                "tgt": {
                    "nodeId": "6062556d-b52b-4d2c-80cc-4cde0ad8c658",
                    "portId": "d9b23659-b30d-4106-9994-2fe0e86c0d1d"
                },
                "condition": "{}"
            },
            {
                "src": {
                    "nodeId": "6062556d-b52b-4d2c-80cc-4cde0ad8c658",
                    "portId": "3cdb543b-0dec-4c9f-b856-296a78b2ae75"
                },
                "tgt": {
                    "nodeId": "43c05110-1741-4526-b78d-5bc548704825",
                    "portId": "f1f4c910-cd19-40a6-ba6c-1b91478175bc"
                },
                "condition": "{}"
            },
            {
                "src": {
                    "nodeId": "43c05110-1741-4526-b78d-5bc548704825",
                    "portId": "1f7cd844-3785-4e0b-b533-7d4ce15c1642"
                },
                "tgt": {
                    "nodeId": "c4d1230b-d5e1-4bdf-9b2a-0f98aaaa28d3",
                    "portId": "4cf7e27d-c4a4-4bde-b734-6e00b46cd63d"
                },
                "condition": "{}"
            }
        ],
        "startNodes": [
            {
                "nodeId": "5e01d6b5-34be-499c-b0d8-e4facddb02f9",
                "type": "root",
                "id": "2e49364d-637e-4d17-9ccc-0498a6c1cf4f"
            }
        ],
    }
    context.pipeline = context.project.pipelines.create(
        pipeline_json=pipeline_json,
        name='test-pipeline-{}'.format(random_5_chars()),
        project_id=context.project.id
    )


@when(u'I install pipeline')
def step_impl(context):
    context.pipeline = context.pipeline.install()
    assert context.pipeline.status == 'Installed'


@then(u'service should have pipeline refs')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.service.id)
    refs = context.service.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'


@then(u'model should have pipeline refs')
def step_impl(context):
    context.model = context.project.models.get(model_id=context.model.id)
    refs = context.model.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'


@then(u'code node package should have pipeline refs')
def step_impl(context):
    code_node: context.dl.CodeNode = [node for node in context.pipeline.nodes if node.node_type == 'code'][0]
    package_name = code_node.namespace.package_name
    package = context.project.packages.get(package_name=package_name)
    refs = package.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'createdBy'


@then(u'code node service should have pipeline refs')
def step_impl(context):
    code_node: context.dl.CodeNode = [node for node in context.pipeline.nodes if node.node_type == 'code'][0]
    service_name = code_node.namespace.service_name
    service = context.project.services.get(service_name=service_name)
    refs = service.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 2
    assert pipeline_ref[0]['metadata']['relation'] == 'createdBy' or pipeline_ref[1]['metadata'][
        'relation'] == 'createdBy'
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy' or pipeline_ref[1]['metadata']['relation'] == 'usedBy'


@then(u'app should have pipeline refs')
def step_impl(context):
    app = context.project.apps.get(app_name=context.app.name)
    refs = app.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'


@then(u'dpk should have pipeline refs')
def step_impl(context):
    dpk = context.project.dpks.get(dpk_name=context.dpk.name)
    refs = dpk.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'


@when(u'I delete pipeline')
def step_impl(context):
    context.pipeline = context.pipeline.delete()


@then(u'service should not have pipeline refs')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.service.id)
    refs = context.service.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0


@then(u'model should not have pipeline refs')
def step_impl(context):
    context.model = context.project.models.get(model_id=context.model.id)
    refs = context.model.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0


@then(u'app should not have pipeline refs')
def step_impl(context):
    app = context.project.apps.get(app_name=context.app.name)
    refs = app.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0


@then(u'dpk should not have pipeline refs')
def step_impl(context):
    dpk = context.project.dpks.get(dpk_name=context.dpk.name)
    refs = dpk.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0
