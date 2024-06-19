from behave import given, when, then
import random
import string


def random_5_chars():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + 'a'


@given(u'a dpk with models and compute configs')
def step_impl(context):
    dpk_json = {
        "displayName": "custom nodes test",
        "name": "compute-configs-{}".format(random_5_chars()),
        "scope": "project",
        "version": "1.0.18",
        "codebase": {
            "type": "git",
            "gitUrl": 'fddfvd',
            "gitTag": "master"
        },
        "attributes": {
            "Provider": "Dataloop",
            "Category": "Pipeline",
            "Pipeline Type": "Node",
            "Node Type": "Other"
        },
        "components": {
            "modules": [
                {
                    "name": "model-adapter-module-config",
                    "entryPoint": "main.py",
                    "className": "ModelAdapter",
                    "computeConfig": "module",
                    "initInputs": [
                        {
                            "type": "Model",
                            "name": "model_entity"
                        }
                    ],
                    "functions": [
                        {
                            "name": "evaluate_model",
                            "input": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                },
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Json",
                                    "name": "filters"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "displayName": "Evaluate a Model",
                            "displayIcon": ""
                        },
                        {
                            "name": "predict_dataset",
                            "input": [
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Json",
                                    "name": "filters"
                                }
                            ],
                            "output": [],
                            "displayName": "Predict Dataset with DQL",
                            "displayIcon": ""
                        },
                        {
                            "name": "predict_items",
                            "input": [
                                {
                                    "type": "Item[]",
                                    "name": "items"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Item[]",
                                    "name": "items"
                                },
                                {
                                    "type": "Annotation[]",
                                    "name": "annotations"
                                }
                            ],
                            "displayName": "Predict Items",
                            "displayIcon": ""
                        },
                        {
                            "name": "train_model",
                            "input": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "displayName": "Train a Model",
                            "displayIcon": ""
                        }
                    ]
                },
                {
                    "name": "model-adapter-function-config",
                    "entryPoint": "main.py",
                    "className": "ModelAdapter",
                    "computeConfig": "module",
                    "initInputs": [
                        {
                            "type": "Model",
                            "name": "model_entity"
                        }
                    ],
                    "functions": [
                        {
                            "name": "evaluate_model",
                            "computeConfig": "function",
                            "input": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                },
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Json",
                                    "name": "filters"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "displayName": "Evaluate a Model",
                            "displayIcon": ""
                        },
                        {
                            "name": "predict_dataset",
                            "input": [
                                {
                                    "type": "Dataset",
                                    "name": "dataset"
                                },
                                {
                                    "type": "Json",
                                    "name": "filters"
                                }
                            ],
                            "output": [],
                            "displayName": "Predict Dataset with DQL",
                            "displayIcon": ""
                        },
                        {
                            "name": "predict_items",
                            "input": [
                                {
                                    "type": "Item[]",
                                    "name": "items"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Item[]",
                                    "name": "items"
                                },
                                {
                                    "type": "Annotation[]",
                                    "name": "annotations"
                                }
                            ],
                            "displayName": "Predict Items",
                            "displayIcon": ""
                        },
                        {
                            "name": "train_model",
                            "computeConfig": "function",
                            "input": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "output": [
                                {
                                    "type": "Model",
                                    "name": "model"
                                }
                            ],
                            "displayName": "Train a Model",
                            "displayIcon": ""
                        }
                    ]
                }
            ],
            "services": [
            ],
            "models": [
                {
                    "computeConfigs": {
                        "deploy": "deploy",
                        "train": "train",
                        "default": "default"
                    },
                    "name": "model-with-compute-configs",
                    "moduleName": "model-adapter-module-config",
                    "description": "test-model-dpk",
                    "scope": "project",
                    "datasetId": context.dataset.id,
                    "tags": [],
                    "status": "created",
                    "labels": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                    "configuration": {
                        "weights_filename": "model.pth",
                        "batch_size": 16,
                        "num_epochs": 10
                    },
                    "inputType": "image",
                    "outputType": "box",
                    "artifacts": [
                        {
                            "type": "link",
                            "url": "https://storage.googleapis.com/model-mgmt-snapshots/ResNet50/model.pth"
                        }
                    ],
                    "metadata": {
                        "system": {
                            "ml": {
                                "defaultConfiguration": {
                                    "weights_filename": "model.pth",
                                    "input_size": 256
                                },
                                "outputType": "box",
                                "inputType": "image",
                                "supportedMethods": [
                                    {
                                        "load": True,
                                        "save": True,
                                        "predict": True,
                                        "deploy": True,
                                        "train": True,
                                        "evaluate": True
                                    }
                                ]
                            },
                            "subsets": {
                                "train": {
                                    "filter": {
                                        "$and": [
                                            {
                                                "dir": "/train"
                                            }
                                        ]
                                    },
                                    "page": 0,
                                    "pageSize": 1000,
                                    "resource": "items"
                                },
                                "validation": {}
                            }
                        }
                    }
                },
                {
                    "name": "model-with-config-in-module",
                    "moduleName": "model-adapter-module-config",
                    "description": "test-model-dpk",
                    "scope": "project",
                    "datasetId": context.dataset.id,
                    "tags": [],
                    "status": "created",
                    "labels": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                    "configuration": {
                        "weights_filename": "model.pth",
                        "batch_size": 16,
                        "num_epochs": 10
                    },
                    "inputType": "image",
                    "outputType": "box",
                    "artifacts": [
                        {
                            "type": "link",
                            "url": "https://storage.googleapis.com/model-mgmt-snapshots/ResNet50/model.pth"
                        }
                    ],
                    "metadata": {
                        "system": {
                            "ml": {
                                "defaultConfiguration": {
                                    "weights_filename": "model.pth",
                                    "input_size": 256
                                },
                                "outputType": "box",
                                "inputType": "image",
                                "supportedMethods": [
                                    {
                                        "load": True,
                                        "save": True,
                                        "predict": True,
                                        "deploy": True,
                                        "train": True,
                                        "evaluate": True
                                    }
                                ]
                            },
                            "subsets": {
                                "train": {
                                    "filter": {
                                        "$and": [
                                            {
                                                "dir": "/train"
                                            }
                                        ]
                                    },
                                    "page": 0,
                                    "pageSize": 1000,
                                    "resource": "items"
                                },
                                "validation": {}
                            }
                        }
                    }
                },
                {
                    "name": "model-with-config-in-function",
                    "moduleName": "model-adapter-function-config",
                    "description": "test-model-dpk",
                    "scope": "project",
                    "datasetId": context.dataset.id,
                    "tags": [],
                    "status": "created",
                    "labels": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                    "configuration": {},
                    "inputType": "image",
                    "outputType": "box",
                    "artifacts": [
                        {
                            "type": "link",
                            "url": "https://storage.googleapis.com/model-mgmt-snapshots/ResNet50/model.pth"
                        }
                    ],
                    "metadata": {
                        "system": {
                            "ml": {
                                "defaultConfiguration": {
                                    "weights_filename": "model.pth",
                                    "input_size": 256
                                },
                                "outputType": "box",
                                "inputType": "image",
                                "supportedMethods": [
                                    {
                                        "load": True,
                                        "save": True,
                                        "predict": True,
                                        "deploy": True,
                                        "train": True,
                                        "evaluate": True
                                    }
                                ]
                            },
                            "subsets": {
                                "train": {
                                    "filter": {
                                        "$and": [
                                            {
                                                "dir": "/train"
                                            }
                                        ]
                                    },
                                    "page": 0,
                                    "pageSize": 1000,
                                    "resource": "items"
                                },
                                "validation": {}
                            }
                        }
                    }
                }
            ],
            "computeConfigs": [
                {
                    "name": "deploy",
                    "runtime": {
                        "podType": "regular-xs",
                        "concurrency": 1,
                        "singleAgent": False,
                        "autoscaler": {
                            "type": "rabbitmq",
                            "minReplicas": 0,
                            "maxReplicas": 0,
                            "queueLength": 1000
                        },
                        "runnerImage": "test-compute-deploy"
                    }
                },
                {
                    "name": "train",
                    "runtime": {
                        "podType": "regular-xs",
                        "concurrency": 1,
                        "singleAgent": False,
                        "autoscaler": {
                            "type": "rabbitmq",
                            "minReplicas": 0,
                            "maxReplicas": 0,
                            "queueLength": 1000
                        },
                        "runnerImage": "test-compute-train"
                    }
                },
                {
                    "name": "default",
                    "runtime": {
                        "podType": "regular-xs",
                        "concurrency": 1,
                        "singleAgent": False,
                        "autoscaler": {
                            "type": "rabbitmq",
                            "minReplicas": 0,
                            "maxReplicas": 0,
                            "queueLength": 1000
                        },
                        "runnerImage": "test-compute-default"
                    }
                },
                {
                    "name": "module",
                    "runtime": {
                        "podType": "regular-xs",
                        "concurrency": 1,
                        "singleAgent": False,
                        "autoscaler": {
                            "type": "rabbitmq",
                            "minReplicas": 0,
                            "maxReplicas": 0,
                            "queueLength": 1000
                        },
                        "runnerImage": "test-compute-from-module"
                    }
                },
                {
                    "name": "function",
                    "runtime": {
                        "podType": "regular-xs",
                        "concurrency": 1,
                        "singleAgent": False,
                        "autoscaler": {
                            "type": "rabbitmq",
                            "minReplicas": 0,
                            "maxReplicas": 0,
                            "queueLength": 1000
                        },
                        "runnerImage": "test-compute-from-function"
                    }
                }
            ]
        }
    }
    dpk = context.dl.Dpk.from_json(_json=dpk_json)
    context.dpk = context.project.dpks.publish(dpk=dpk)
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.dpk)
    else:
        context.feature.dpks = [context.dpk]


@given(u'pipeline with train model')
def step_impl(context):
    pipeline_json = {
        "name": "test-pipeline-{}".format(random_5_chars()),
        "projectId": context.project.id,
        "nodes": [
            {
                "id": "6bdab0b3-07ed-4402-8984-961021368b1d",
                "inputs": [
                    {
                        "portId": "2ed2fb72-08ea-456f-880f-4b8208e6d174",
                        "nodeId": "2ed2fb72-08ea-456f-880f-4b8208e6d174",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "input"
                    }
                ],
                "outputs": [
                    {
                        "portId": "ef7a6583-a6ad-47dd-8e9e-9573014e3be7",
                        "nodeId": "ef7a6583-a6ad-47dd-8e9e-9573014e3be7",
                        "type": "Model",
                        "name": "model",
                        "displayName": "model",
                        "io": "output"
                    }
                ],
                "metadata": {
                    "position": {
                        "x": 9905.91568182221,
                        "y": 9852.332327637567,
                        "z": 0
                    },
                    "repeatable": True
                },
                "name": "Train Model",
                "type": "ml",
                "namespace": {
                    "functionName": "train",
                    "projectName": "aaron-test-integrations",
                    "serviceName": "model-mgmt-app-train",
                    "moduleName": "model-mgmt-app-train",
                    "packageName": "model-mgmt-app"
                },
                "projectId": "0811a1e6-2023-4fbc-91f2-3ee263544924"
            }
        ],
        "connections": [
        ],
        "startNodes": [
            {
                "nodeId": "6bdab0b3-07ed-4402-8984-961021368b1d",
                "type": "root",
                "id": "b0d148dc-6c3c-4edb-bd40-7dd7b89b3d08"
            }
        ],
    }
    context.pipeline = context.project.pipelines.create(
        pipeline_json=pipeline_json,
        name='test-pipeline-{}'.format(random_5_chars()),
        project_id=context.project.id
    )
    context.to_delete_pipelines_ids.append(context.pipeline.id)


@given(u'models are set in context')
def step_impl(context):
    models = context.project.models.list()
    for model in models.items:
        if model.name == 'model-with-compute-configs':
            context.model_with_compute_configs = model
        if model.name == 'model-with-config-in-module':
            context.model_with_config_in_module = model
        if model.name == 'model-with-config-in-function':
            context.model_with_config_in_function = model


@when(u'I execute pipeline on model with compute configs')
def step_impl(context):
    pipe_execution = context.pipeline.execute({"model": context.model_with_compute_configs.id})
    assert pipe_execution.status != 'failed', "TEST FAILED: Execution status is 'failed', Please check if pipeline cycle execution has transitionErrors"


@then(u'service should use model train compute config')
def step_impl(context):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.SERVICE)
    filters.add(field='metadata.ml.modelId', values=context.model_with_compute_configs.id)
    s = context.project.services.list(filters=filters).items[0]
    assert s.runtime.runner_image == 'test-compute-train'


@when(u'I execute pipeline on model with config in module')
def step_impl(context):
    pipe_execution = context.pipeline.execute({"model": context.model_with_config_in_module.id})
    assert pipe_execution.status != 'failed', "TEST FAILED: Execution status is 'failed', Please check if pipeline cycle execution has transitionErrors"


@then(u'service should use model module compute config')
def step_impl(context):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.SERVICE)
    filters.add(field='metadata.ml.modelId', values=context.model_with_config_in_module.id)
    s = context.project.services.list(filters=filters).items[0]
    assert s.runtime.runner_image == 'test-compute-from-module'


@when(u'I execute pipeline on model with config in function')
def step_impl(context):
    pipe_execution = context.pipeline.execute({"model": context.model_with_config_in_function.id})
    assert pipe_execution.status != 'failed', "TEST FAILED: Execution status is 'failed', Please check if pipeline cycle execution has transitionErrors"


@then(u'service should use model function compute config')
def step_impl(context):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.SERVICE)
    filters.add(field='metadata.ml.modelId', values=context.model_with_config_in_function.id)
    s = context.project.services.list(filters=filters).items[0]
    assert s.runtime.runner_image == 'test-compute-from-function'
