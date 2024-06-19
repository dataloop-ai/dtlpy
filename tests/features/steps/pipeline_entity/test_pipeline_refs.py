from behave import given, when, then
import random
import string
import time


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


@then(u'service should have pipeline refs and cannot be uninstall')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.service.id)
    refs = context.service.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'
    try:
        context.service.delete()
    except context.dl.exceptions.FailedDependency as e:
        assert e.status_code == '424', f"TEST FAILED: Expected: '{424}' Actual: {e.status_code}"
        assert f"Unable to delete service '{context.service.name}'" in e.message, f"TEST FAILED: Expected: Unable to delete service '{context.service.name}'\nActual: {e.message}"


@then(u'model should have pipeline refs and cannot be deleted')
def step_impl(context):
    context.model = context.project.models.get(model_id=context.model.id)
    refs = context.model.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'
    try:
        context.model.delete()
    except context.dl.exceptions.FailedDependency as e:
        assert e.status_code == '424', f"TEST FAILED: Expected: '{424}' Actual: {e.status_code}"
        assert f"Unable to delete model '{context.model.name}'" in e.message, f"TEST FAILED: Expected: Unable to delete model '{context.model.name}'\nActual: {e.message}"


@then(u'code node package should have pipeline refs')
def step_impl(context):
    code_node: context.dl.CodeNode = [node for node in context.pipeline.nodes if node.node_type == 'code'][0]
    package_name = code_node.namespace.package_name
    package = context.project.packages.get(package_name=package_name)
    refs = package.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'createdBy'


@then(u'code node service should have pipeline refs and cannot be uninstall')
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
    try:
        context.service.delete()
    except context.dl.exceptions.FailedDependency as e:
        assert e.status_code == '424', f"TEST FAILED: Expected: '{424}' Actual: {e.status_code}"
        assert f"Unable to delete service '{context.service.name}'" in e.message, f"TEST FAILED: Expected: Unable to delete service '{context.service.name}'\nActual: {e.message}"


@then(u'app should have pipeline refs and cannot be uninstall')
def step_impl(context):
    app = context.project.apps.get(app_name=context.app.name)
    refs = app.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'
    try:
        app.uninstall()
    except context.dl.exceptions.FailedDependency as e:
        assert e.status_code == '424', f"TEST FAILED: Expected: '{424}' Actual: {e.status_code}"
        assert f"Unable to delete app '{app.name}'" in e.message, f"TEST FAILED: Expected: Unable to delete app '{app.name}'\nActual: {e.message}"


@then(u'dpk should have pipeline refs and cannot be deleted')
def step_impl(context):
    dpk = context.project.dpks.get(dpk_name=context.dpk.name)
    refs = dpk.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 1
    assert pipeline_ref[0]['metadata']['relation'] == 'usedBy'
    try:
        dpk.delete()
    except context.dl.exceptions.FailedDependency as e:
        assert e.status_code == '424', f"TEST FAILED: Expected: '{424}' Actual: {e.status_code}"
        assert f"Unable to delete dpk '{dpk.display_name}'" in e.message, f"TEST FAILED: Expected: Unable to delete dpk '{dpk.display_name}'\nActual: {e.message}"


@when(u'I delete pipeline')
def step_impl(context):
    context.pipeline = context.pipeline.delete()


@then(u'service should not have pipeline refs and uninstall service "{flag}"')
def step_impl(context, flag):
    context.service = context.project.services.get(service_id=context.service.id)
    refs = context.service.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0
    if flag == 'True':
        try:
            context.service.delete()
        except Exception as e:
            assert False, f"TEST FAILED: {e}"


@then(u'model should not have pipeline refs and delete model "{flag}"')
def step_impl(context, flag):
    context.model = context.project.models.get(model_id=context.model.id)
    refs = context.model.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0
    if flag == 'True':
        try:
            context.model.delete()
            context.model_count -= 1
        except Exception as e:
            assert False, f"TEST FAILED: {e}"


@then(u'app should not have pipeline refs and uninstall app "{flag}"')
def step_impl(context, flag):
    app = context.project.apps.get(app_name=context.app.name)
    refs = app.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0
    if flag == 'True':
        try:
            app.uninstall()
        except Exception as e:
            assert False, f"TEST FAILED: {e}"


@then(u'dpk should not have pipeline refs and delete dpk "{flag}"')
def step_impl(context, flag):
    dpk = context.project.dpks.get(dpk_name=context.dpk.name)
    refs = dpk.metadata.get('system', {}).get('refs', [])
    pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
    assert len(pipeline_ref) == 0
    if flag == 'True':
        try:
            dpk.delete()
        except Exception as e:
            assert False, f"TEST FAILED: {e}"


@then(u'I Should be able to uninstall service')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.service.id)
    try:
        context.service.delete()
    except Exception as e:
        assert False, f"TEST FAILED: {e}"


@then(u'I Should be able to delete model')
def step_impl(context):
    context.model = context.project.models.get(model_id=context.model.id)
    try:
        context.model.delete()
        context.model_count -= 1
    except Exception as e:
        assert False, f"TEST FAILED: {e}"


@then(u'I Should be able to uninstall app')
def step_impl(context):
    app = context.project.apps.get(app_name=context.app.name)
    try:
        app.uninstall()
    except Exception as e:
        assert False, f"TEST FAILED: {e}"


@then(u'I Should be able to delete dpk')
def step_impl(context):
    dpk = context.project.dpks.get(dpk_name=context.dpk.name)
    try:
        dpk.delete()
    except Exception as e:
        assert False, f"TEST FAILED: {e}"


@given(u'I have a pipeline with train node and evaluate node')
def step_impl(context):
    models = context.project.models.list().items
    context.model_for_train = [m for m in models if m.status == context.dl.ModelStatus.CREATED][0]
    context.model_for_evaluate = \
        [m for m in models if m.status in [context.dl.ModelStatus.TRAINED, context.dl.ModelStatus.PRE_TRAINED]][0]
    pipeline_name = 'pipeline-{}'.format(random_5_chars())
    pipeline_json = {
        "name": pipeline_name,
        "projectId": context.project.id,
        "nodes": [
            {
                "id": "0d1575d6-c222-4916-9743-2f8e3e9d543c",
                "inputs": [
                    {
                        "portId": "794cbcc4-d0bd-4c58-a3be-ce0348e3bc25",
                        "nodeId": "794cbcc4-d0bd-4c58-a3be-ce0348e3bc25",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "a14297d7-75ee-42ff-ba79-26e85e313f3d",
                        "nodeId": "a14297d7-75ee-42ff-ba79-26e85e313f3d",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10172.3515625,
                        "y": 9719,
                        "z": 0
                    },
                    "repeatable": True
                },
                "name": "Train Model",
                "type": "ml",
                "namespace": {
                    "functionName": "train",
                    "projectName": "Test-Project1",
                    "serviceName": "model-mgmt-app-train",
                    "moduleName": "model-mgmt-app-train",
                    "packageName": "model-mgmt-app"
                },
                "projectId": context.project.id
            },
            {
                "id": "c78f7330-5894-460d-802f-28412f621aed",
                "inputs": [
                    {
                        "portId": "d2a0a760-fde2-4c7a-91c7-27d098bbc207",
                        "nodeId": "d2a0a760-fde2-4c7a-91c7-27d098bbc207",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "input",
                        "defaultValue": context.model_for_evaluate.id
                    },
                    {
                        "portId": "fc462fe9-95ac-4ed4-9428-5835c344984c",
                        "nodeId": "fc462fe9-95ac-4ed4-9428-5835c344984c",
                        "type": "Dataset",
                        "name": "dataset",
                        "displayName": "dataset",
                        "io": "input"
                    },
                    {
                        "portId": "8f3d8f25-3037-468a-918c-49be14287182",
                        "nodeId": "8f3d8f25-3037-468a-918c-49be14287182",
                        "type": "Json",
                        "name": "filters",
                        "displayName": "filters",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "c47079e9-220e-4f7f-b91e-9818dc7c7805",
                        "nodeId": "c47079e9-220e-4f7f-b91e-9818dc7c7805",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "output"
                    },
                    {
                        "portId": "502caf71-9c93-4214-92ae-8f34e69dc88f",
                        "nodeId": "502caf71-9c93-4214-92ae-8f34e69dc88f",
                        "type": "Dataset",
                        "name": "dataset",
                        "displayName": "dataset",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 10172.3515625,
                        "y": 9896,
                        "z": 0
                    }
                },
                "name": "Evaluate Model",
                "type": "ml",
                "namespace": {
                    "functionName": "evaluate",
                    "projectName": "Test-Project1",
                    "serviceName": "model-mgmt-app-evaluate",
                    "moduleName": "model-mgmt-app-evaluate",
                    "packageName": "model-mgmt-app"
                },
                "projectId": context.project.id
            },
            {
                "id": "d4fe0be0-243a-49ab-bfbf-678248234729",
                "inputs": [

                ],
                "outputs": [
                    {
                        "portId": "3134969b-12c8-4e1c-b7e4-42afd61114cc",
                        "nodeId": "3134969b-12c8-4e1c-b7e4-42afd61114cc",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "output"
                    },
                    {
                        "portId": "8cd0d65d-9398-4ce3-8189-3e9f46d69e03",
                        "nodeId": "8cd0d65d-9398-4ce3-8189-3e9f46d69e03",
                        "type": "Dataset",
                        "name": "dataset",
                        "displayName": "dataset",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 9825.3515625,
                        "y": 9802,
                        "z": 0
                    },
                    "codeApplicationName": "first-{}".format(random_5_chars())
                },
                "name": "code",
                "type": "code",
                "namespace": {
                    "functionName": "run",
                    "projectName": "Test-Project1",
                    "serviceName": "first",
                    "moduleName": "code_module",
                    "packageName": "first"
                },
                "projectId": context.project.id,
                "config": {
                    "package": {
                        "code": "import dtlpy as dl\n\n\nclass ServiceRunner:\n\n    def run(self, context: dl.Context):\n        dataset = context.project.datasets.list()[0]\n        model = [m for m in context.project.models.list().items if m.status == 'created'][0]\n        return [model, dataset]",
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
                    "nodeId": "d4fe0be0-243a-49ab-bfbf-678248234729",
                    "portId": "3134969b-12c8-4e1c-b7e4-42afd61114cc"
                },
                "tgt": {
                    "nodeId": "0d1575d6-c222-4916-9743-2f8e3e9d543c",
                    "portId": "794cbcc4-d0bd-4c58-a3be-ce0348e3bc25"
                },
                "condition": "{}"
            },
            {
                "src": {
                    "nodeId": "d4fe0be0-243a-49ab-bfbf-678248234729",
                    "portId": "8cd0d65d-9398-4ce3-8189-3e9f46d69e03"
                },
                "tgt": {
                    "nodeId": "c78f7330-5894-460d-802f-28412f621aed",
                    "portId": "fc462fe9-95ac-4ed4-9428-5835c344984c"
                },
                "condition": "{}"
            }
        ],
        "startNodes": [
            {
                "nodeId": "d4fe0be0-243a-49ab-bfbf-678248234729",
                "type": "root",
                "id": "68bfab61-7677-4854-a6a6-cb40228a939a"
            }
        ]
    }
    context.pipeline = context.project.pipelines.create(
        name=pipeline_name,
        pipeline_json=pipeline_json,
        project_id=context.project.id
    )
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@given(u'I pause pipeline when executions are created')
def step_impl(context):
    interval = 5
    timeout_seconds = 60 * 5
    start = time.time()
    while time.time() - start < timeout_seconds:
        filters = context.dl.Filters(resource=context.dl.FiltersResource.EXECUTION)
        filters.add(field='pipeline.id', values=context.pipeline.id)
        executions = context.project.executions.list(filters=filters)
        if len(executions.items) == 3:
            context.pipeline.pause()
            context.pipeline = context.project.pipelines.get(pipeline_id=context.pipeline.id)
            break
        time.sleep(interval)
    assert context.pipeline.status == context.dl.CompositionStatus.UNINSTALLED


@then(u'model services should still have refs')
def step_impl(context):
    model_services = [s for s in context.project.services.list().items if 'ml' in s.metadata]
    for model_service in model_services:
        refs = model_service.metadata.get('system', {}).get('refs', [])
        pipeline_ref = [ref for ref in refs if ref['id'] == context.pipeline.id]
        assert pipeline_ref.__len__() == 2, 'model service {} should have 2 refs but has {}'.format(
            model_service.name, pipeline_ref.__len__())
        used_by_ref = [ref for ref in pipeline_ref if ref['metadata']['relation'] == 'usedBy']
        assert used_by_ref.__len__() == 1, 'model service {} should have 1 usedBy ref but has {}'.format(
            model_service.name, used_by_ref.__len__())
        created_by_ref = [ref for ref in pipeline_ref if ref['metadata']['relation'] == 'createdBy']
        assert created_by_ref.__len__() == 1, 'model service {} should have 1 createdBy ref but has {}'.format(
            model_service.name, created_by_ref.__len__())
