Getting Started With FaaS
==========================

In this tutorial you will generate a basic package, modify it, and test it locally

Hello World FaaS Example
-------------------------
Before starting:
Checkout to a local project

CLI

.. code-block:: python

    $ dlp projects checkout --project-name <project_name/project_id>

SDK

.. code-block:: python

    import dtlpy as dl
    dl.projects.checkout('project name')

Generate package source code at the current directory

CLI

.. code-block:: python

   $ dlp packages generate [optional --plugin-name "my-first-package"]

SDK

.. code-block:: python

   dl.packages.generate(name="my-first-package")


The above command should generate the following files in the current working directory:

    1. package.json      - package info
    2. main.py           - package  source code
    3. mock.json         - package  inputs for local testing
    4. service.json      - service info
    5. .gitignore        - files to ignore when pushing package to cloud

Now, lest push the package

CLI

.. code-block:: python

   $ dlp packages push [optional --checkout]

SDK

.. code-block:: python

   dl.packages.push(checkout=True)

This will push the package, and create a package entity in the database.
The optional param "checkout" means the package with be saved in state.

Next, we would like to deploy the package to the Dataloop FaaS Cloud

CLI

.. code-block:: python

   $ dlp packages deploy [optional --checkout]

SDK

.. code-block:: python

   dl.packages.deploy_from_local_folder(checkout=True)


Now we have an up and running service in the cloud.

We can now execute a function in that service:

CLI

.. code-block:: python

   $ dlp services invoke

SDK

.. code-block:: python

   dl.services.get().invoke()


Advanced FaaS
=====================
Plugin Json
---------------------
Before starting:
Checkout to a local project

CLI

.. code-block:: python

    $ dlp projects checkout --project-name <project_name/project_id>

SDK

.. code-block:: python

    import dtlpy as dl
    dl.projects.checkout('project name')

Generate package source code at the current directory

CLI

.. code-block:: python

   $ dlp packages generate [optional --plugin-name "my-first-package"]

SDK

.. code-block:: python

   dl.packages.generate(name="my-first-package")


The above command should generate the following files in the current working directory:

    1. package.json      - package info
    2. main.py           - package  source code
    3. mock.json         - package  inputs for local testing
    4. service.json      - service info
    5. .gitignore        - files to ignore when pushing package to cloud


Now lets create a function the receives an item input and annotates it.
To do so, we first need to edit the source code in file main.py:

.. code-block:: python

    import dtlpy as dl
    import logging
    logger = logging.getLogger(name=__name__)


    class ServiceRunner(dl.BaseServiceRunner):
        """
        Package runner class

        """

        def __init__(self, **kwargs):
            """
            Init package attributes here

            :param kwargs: config params
            :return:
            """

        def run(self, item, progress=None):
            """
            Write your main package service here

            :param progress: Use this to update the progress of your package
            :return:
            """
            # create annotation
            ann = dl.Annotation.new(
                annotation_definition=dl.Classification(label='completed'),
                item=item
            )
            ann.upload()

            # update session progress
            progress.update(status='inProgress', progress=100)


Run method receives, by default, a progress object which allows us to update session progress.

| DO NOT MAKE CHANGES TO THE main.py or any other entry_point LAYOUT!
| Changes we are allowed to make are:
|    1. function params (as long as it still receive progress and inputs defined in package.json).
|    2. Code within run and init methods.
|    3. Addition of other methods and classes
|    4. Additional imports

Now we need to let the package know it expects an item input and push it to the cloud:

CLI

First edit the run function inputs in the default module:

.. code-block:: python

   {
        "name": "default_package",
        "modules": [
            {
                "name": "default_module",
                "entryPoint": "main.py",
                "initInputs": [],
                "functions": [
                    {
                        "name": "run",
                        "description": "this description for your service",
                        "input": [
                            {
                                "name": "item",
                                "type": "Item"
                            }
                        ],
                        "output": []
                    }
                ]
            }
        ]
    }


Then push the package
.. code-block:: python

   $ dlp packages push --checkout

SDK

.. code-block:: python

    inputs = dl.FunctionIO(type=dl.PackageInputType.ITEM, name='item')
    function = dl.PackageFunction(inputs=inputs)
    module = dl.PackageModule(functions=function)

    package = dl.packages.push(modules=module, checkout=True)


Next, we would like to deploy the package to the Dataloop FaaS Cloud with our oun configuration:

CLI

Edit Service configuration in the service.json

.. code-block::

    {
      "name": "service-name",               # service name
      "packageName": "default_package",     # package name
      "packageRevision": "latest",          # what package version to run?
      "runtime": {
        "gpu": false,                       # Does the service require GPU?
        "replicas": 1,                      # How many replicas should the service create
        "concurrency": 6,                   # How many executions can run simultaneously?
        "runnerImage": ""                   # You can provide your own docker image for the service to run on.
      },
      "triggers": [],                       # List of triggers to trigger service
      "initParams": {},                     # Does your init method expects input if it does provide it here.
      "moduleName": "default_module"        # Which module to deploy?
    }

Deploy:

.. code-block:: python

   $ dlp packages deploy [optional --checkout]

SDK

.. code-block:: python

   package.deploy(service_name=None, runtime={ "gpu": False,
                                                "replicas": 1,
                                                "concurrency": 6,
                                                "runnerImage": "" })


Now we have an up and running service in the cloud.

We can now execute a function in that service:

CLI

.. code-block:: python

   $ dlp services invoke --item-id <item id>

SDK

.. code-block:: python

   dl.services.get().invoke(execution_input=dl.FunctionIO(name='item', value=<item id>, type='Item'))


Testing Plugin
---------------------

Your mock.json exists in-order to allow local package tests.
By providing package inputs in the "input" field of mock.json, you can perform:

CLI

.. code-block:: python

   $ dlp plugins test

SDK

.. code-block:: python

    dl.plugins.test_local_plugin()

This will run the init method followed by the run method with params provided in the mock.json.
When running the command from the SDK make sure you're either running the code from the plugin working directory,
or providing param cwd of the plugin working directory.

For example:

.. code-block:: python

    {
      "inputs": [
        {
          "name": "item",
          "value": {
            "item_id": "5d8b1d1bba74a0f7717c500b"
          }
        }
      ]
    }

| the run method will receive item with id provided.

Triggers
===========

Now that we have a running service, we can trigger it automatically when something happens,

we can do so by creating a trigger.

Triggers can work on items, datasets or annotations and be triggered upon creation, update or deletion.

Create a trigger:

SDK

.. code-block:: python

    import dtlpy as dl
    ##################################################################
    # create trigger for when item is uploaded to directory "/train" #
    ##################################################################

    # create filter
    filters = dl.Filters(field='dir', values='/train')

    # create trigger
    trigger = service.triggers.create(
            service_id=service.id,
            resource=dl.TriggerResource.ITEM,
            actions=dl.TriggerAction.CREATED,
            name='training-trigger',
            filters=filters,
            execution_mode=dl.TriggerExecutionMode.ONCE,
            function_name='run'
        )


To create a trigger using the CLI, simply add the trigger to the service.json before deploying the service:

CLI

.. code-block::

    {
      "name": "service-name",               # service name
      "packageName": "default_package",     # package name
      "packageRevision": "latest",          # what package version to run?
      "runtime": {
        "gpu": false,                       # Does the service require GPU?
        "replicas": 1,                      # How many replicas should the service create
        "concurrency": 6,                   # How many executions can run simultaneously?
        "runnerImage": ""                   # You can provide your own docker image for the service to run on.
      },
      "triggers": [
                {
                  "name": "trigger-name",
                  "filter": {'$and': [{'dir': '/train'}, {'hidden': False}, {'type': 'file'}]},
                  "resource": "Item",
                  "actions": [
                    "Created"
                  ],
                  "active": true,
                  "function": "run",
                  "executionMode": "Once"
                }
      ],                       # List of triggers to trigger service
      "initParams": {},                     # Does your init method expects input if it does provide it here.
      "moduleName": "default_module"        # Which module to deploy?
    }

Or, if you already have an existing service you can attach a trigger to it by:

.. code-block:: python

    $   triggers create --package-name "default_package" --service-name "service-name" --name "trigger-name"
        --filters '{"$and": [{"dir": "/train"}, {"hidden": False}, {"type": "file"}]}' --function-name 'run'
        --resource "Item" --actions "Created"

Modules and Functions
=======================
One package can provide different modules.
A module is a scheme contains functions, entry point and init params that construct a package implementation.
Every package has at least one module that has at least one function.

The default module is:

.. code-block::

    {
        "name": "default_module",          # module name
        "entryPoint": "main.py",           # the module entry point which includes its main class and methods
        "initInputs": [],                  # expected init params at deployment time
        "functions": [                     # list of module functions that can be executed from remote
            {
                "name": "run",             # function name - must be the same as the actual method name in signature
                "description": "",         # optional -  function description
                "input": [                 # expected function params
                    {
                        "name": "item",    # input name - identical to input param name in signature
                        "type": "Item"     # Item / Dataset / Annotation / Json
                    }
                ],
                "output": []               # not implemented - keep blank
            }
        ]
    }

Example:
---------
First entry point
file name: dataset_auto_ml.py:

.. code-block:: python

    import dtlpy as dl
    import logging
    from .models_loader import ModelLoader

    logger = logging.getLogger(name=__name__)


    class ServiceRunner(dl.BaseServiceRunner):
        """
        Package runner class

        """

        def __init__(self, **kwargs):
            """
            Init package attributes here

            :param kwargs: config params
            :return:
            """
            model_name = kwargs['model_name']
            self.model = ModelLoader(model_name=model_name)

        def train(self, dataset, progress=None):
            # download items
            filters = dl.Filters(field='annotated', values=True)
            items_path = dataset.items.download(filters=filters)
            annotations_path = dataset.download_annotations()

            # train model
            self.model.train(annotations_path=annotations_path, items_path=items_path)

            # update execution progress
            progress.update(status='completed', progress=100)

        def predict(self, dataset, progress=None):
            # download items
            filters = dl.Filters(field='annotated', values=False)
            pages = dataset.items.list(filters=filters)

            # predict and upload
            page_counter = 0
            for page in pages:
                for item in page:
                    item_io_buffer = item.download(save_locally=False)
                    annotations = self.model.predict(items=item_io_buffer)
                    item.annotations.upload(annotations=annotations)

                # update execution progress
                page_counter += 1
                percent_completed = round((page_counter/pages.total_pages_count) * 100)
                progress.update(status='inProgress', progress=percent_completed)

            # update execution progress
            progress.update(status='completed', progress=100)


First entry point
in file name: single_item_auto_ml.py:

.. code-block:: python

    import dtlpy as dl
    import logging
    from .models_loader import ModelLoader

    logger = logging.getLogger(name=__name__)


    class ServiceRunner(dl.BaseServiceRunner):
        """
        Package runner class

        """

        def __init__(self, **kwargs):
            """
            Init package attributes here

            :param kwargs: config params
            :return:
            """
            model_name = kwargs['model_name']
            self.model = ModelLoader(model_name=model_name)

        def train(self, item, progress=None):
            # download item
            item_path = item.download()
            annotations_path = item.annotations.download()

            # train model
            self.model.train_single_item(annotations_path=annotations_path, items_path=items_path)

            # update execution progress
            progress.update(status='completed', progress=100)

        def predict(self, item, progress=None):
            # download item and predict
            item_io_buffer = item.download(save_locally=False)
            annotations = self.model.predict(items=item_io_buffer)
            item.annotations.upload(annotations=annotations)

            # update execution progress
            progress.update(status='completed', progress=100)


When pushing this package we need to defines its modules:

CLI

Edit package.json:

.. code-block:: python

   {
        "name": "auto_ml",
        "modules": [
            {
                "name": "dataset_auto_ml",
                "entryPoint": "dataset_auto_ml.py",
                "initInputs": [
                    {
                        "type": "Json",
                        "name": "model_name"
                    }
                ],
                "functions": [
                    {
                        "name": "train",
                        "description": "Train entire dataset",
                        "input": [
                            {
                                "name": "dataset",
                                "type": "Dataset"
                            }
                        ]
                    },
                    {
                        "name": "predict",
                        "description": "Predict entire dataset",
                        "input": [
                            {
                                "name": "dataset",
                                "type": "Dataset"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "single_item_auto_ml",
                "entryPoint": "single_item_auto_ml.py",
                "initInputs": [
                    {
                        "type": "Json",
                        "name": "model_name"
                    }
                ],
                "functions": [
                    {
                        "name": "train",
                        "description": "Train single item",
                        "input": [
                            {
                                "name": "item",
                                "type": "Item"
                            }
                        ]
                    },
                    {
                        "name": "predict",
                        "description": "Predict single item",
                        "input": [
                            {
                                "name": "item",
                                "type": "Item"
                            }
                        ]
                    }
                ]
            }
        ]
    }


Then push the package
.. code-block:: python

   $ dlp packages push


SDK

.. code-block:: python

    # define init input
    init_inputs = dl.FunctionIO(type=dl.PackageInputType.JSON, name='model_name')

    # define item input spec
    item_inputs = dl.FunctionIO(type=dl.PackageInputType.ITEM, name='item')

    # define first module functions
    item_train_function = dl.PackageFunction(inputs=item_inputs, name='train', description='Train single item')
    item_predict_function = dl.PackageFunction(inputs=item_inputs, name='predict', description='Predict single item')

    # define first module
    item_auto_ml_module = dl.PackageModule(functions=[item_train_function, item_predict_function],
                                           name='single_item_auto_ml',
                                           entry_point='single_item_auto_ml.py', init_inputs=init_inputs)

    # define dataset input spec
    dataset_inputs = dl.FunctionIO(type=dl.PackageInputType.DATASET, name='dataset')

    # define second module functions
    dataset_train_function = dl.PackageFunction(inputs=dataset_inputs, name='train', description='Train entire dataset')
    dataset_predict_function = dl.PackageFunction(inputs=dataset_inputs, name='predict',
                                                  description='Predict entire dataset')

    # define second module
    dataset_auto_ml_module = dl.PackageModule(functions=[dataset_train_function, dataset_predict_function],
                                              name='dataset_auto_ml',
                                              entry_point='dataset_auto_ml.py', init_inputs=init_inputs)

    # push package
    package = dl.packages.push(package_name='auto_ml', modules=[item_auto_ml_module, dataset_auto_ml_module])


Deploying a service requires init input and module name:


CLI

Edit Service configuration in the service.json

.. code-block::

    {
      "name": "item-auto-ml-service",            # service name
      "packageName": "auto_ml",                  # package name
      "packageRevision": "latest",               # what package version to run?
      "runtime": {
        "gpu": true,                             # Does the service require GPU?
        "replicas": 1,                           # How many replicas should the service create
        "concurrency": 1,                        # How many executions can run simultaneously?
        "runnerImage": "gpu/image/main:latest"   # You can provide your own docker image for the service to run on.
      },
      "triggers": [],                            # List of triggers to trigger service
      "initParams": {                            # Provide init param value
            "model_name": "my_model"
      },
      "moduleName": "single_item_auto_ml"        # Which module to deploy?
    }

Deploy:

.. code-block:: python

   $ dlp packages deploy [optional --checkout]

SDK

.. code-block:: python

   init_inputs = dl.FunctionIO(type=dl.PackageInputType.JSON, name='model_name', value='my_model')

   package.deploy(service_name=None,
                   init_input=init_inputs,
                   service_name='single-item-auto-ml-service',
                   runtime={
                        "gpu": True,
                        "replicas": 1,
                        "concurrency": 1,
                        "runnerImage": "" })

