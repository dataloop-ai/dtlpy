Starting With Plugins
=====================

In this tutorial you will generate a basic plugin, modify it, and test it locally

Bootstraping the plugin
-----------------------
Before starting run

Checkout to a local project and dataset

CLI

.. code-block:: python

    $ dlp projects checkout <project_name/project_id>
    $ dlp datasets checkout <dataset_name/dataset_id>

SDK

.. code-block:: python

    import dtlpy as dl
    dl.projects.checkout('project name')
    dl.datasets.checkout('dataset name')

Create a Plugin at the current directory

CLI

.. code-block:: python

   $ dlp plugins generate --plugin-name

SDK

.. code-block:: python

   dl.plugins.generate()

The above command should generate the following files in the current working directory:

    1. plugin.json       -  plugin info
    2. main.py           - plugin source code
    3. mock.json         - plugin inputs for local testing
    4. deployment.json   - deployment info
    5. .gitignore        - files to ignore when pushing plugin to cloud

Developing the plugin
=====================
Plugin Json
---------------------
The plugin.json should look something like this:

.. code-block:: python

    {
        "inputs": [
            {
                "type": "Item",
                "name": "item"
            }
        ],
        "outputs": [
        ],
        "name": "myPlugin"
    }

It defines the plugin inputs, outputs and name.

In this case:
    The plugin name is: myPlugin and it expects an item input.

Input can be of types, item, dataset, annotation and json
The value of an dataset entity should be in the form:

.. code-block:: python

    {
      "dataset_id": <dataset_id>
    }

The value of an item entity should be in the form:

.. code-block:: python

    {
      "dataset_id": <dataset_id>,
      "item_id": <item_id>
    }

The value of an annotation entity should be in the form:

.. code-block:: python

    {
      "dataset_id": <dataset_id>,
      "item_id": <item_id>,
      "annotation_id": <annotation_id>
    }

The value of a Json entity can be any json serializable value.

Plugin Source Code
---------------------
Your main.py file should look something like this:

.. code-block:: python

    import dtlpy as dl
    import logging
    logger = logging.getLogger(name=__name__)

    class PluginRunner(dl.BasePluginRunner):
        """
        Plugin runner class

        """
        def __init__(self, **kwargs):
            """
            Init plugin attributes here
            
            :param kwargs: config params
            :return:
            """
            self.message = kwargs['message']

        def run(self, item, progress=None):
            """
            Write your main plugin function here

            :param progress: Use this to update the progress of your plugin
            :return:
            """
            # update session progress
            progress.update(status='inProgress', progress=0)

            # change metadata
            item.metadata['message']['user']['firstPlugin'] = self.message
            item.update()

            # update session progress
            progress.update(status='inProgress', progress=50)

            # create annotation
            ann = dl.Annotation.new(
                annotation_definition=dl.Classification(label='completed'),
                item=item
            )
            ann.upload()

            # update session progress
            progress.update(status='inProgress', progress=100)

    if __name__ == "__main__":
        """
        Run this main to locally debug your plugin
        """
        # config param for local testing
        kwargs = dict()
        dl.plugins.test_local_plugin(kwargs)

| The plugin configuration will run the code in init method once.
| And each plugin session will perform the code in the run method.

In this case:
    | The init will set global attribute 'message' and the session will add this
    | message to the item's metadata, then, it will create a classification annotation
    | and upload it to the item.

Run method receives a progress object which allows us to update session progress.

| DO NOT MAKE CHANGES TO THE main.py LAYOUT!
| Changes we are allowed to make are:
|    1. run() params (as long as it still receive progress and inputs defined in plugin.json).
|    2. Code within run and init methods.
|    3. Addition of other methods and classes
|    4. Additional imports

Testing Plugin
---------------------

Your mock.json exists in-order to allow local plugin tests.
By providing plugin inputs in the "input" field of mock.json
And providing init params in the "config" field of mock.json
You can perform:

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
            "dataset_id": "5d8b1d0ecb5bbd508b64f491",
            "item_id": "5d8b1d1bba74a0f7717c500b"
          }
        }
      ],
      "config": {
        "message": "My first plugin"
      }
    }

| the init method will receive {"message": "My first plugin"}
| and run method will receive item with id provided from dataset with id provided.

| Meaning, this item's metadata will be updated with the following:
|   "firstPlugin" = "My first plugin"

You can also provide any JSON serializable inputs:

.. code-block:: python

    {
      "inputs": [
        {
          "name": "string_param",
          "value": 'string input'
        }
      ]
    }

Deploy to cloud
=====================
First push the pluging by performing:

CLI

.. code-block:: python

   $ dlp plugins push

SDK

.. code-block:: python

   project = dl.projects.get()
   project.plugins.push(src_path='path/to/plugin/directoy')


When using the SDK to push a plugin you can ignore the plugin.json file and provide the plugin params manually:

SDK

.. code-block:: python

   inputs = [
    dl.PluginInput(name='item', type=dl.PluginInputType.ITEM),
    dl.PluginInput(name='config', type=dl.PluginInputType.JSON)
    ]

   plugin = project.plugins.push(
                        src_path='path/to/plugin/directoy',
                        inputs=inputs,
                        plugin_name="my-first-plugin")

Secondly, edit the deployment.json file:

.. code-block:: python

    {
    "name": "deployment-json",
    "plugin": "deploymentJsonPlugin",
    "runtime": {
      "gpu": false,
      "replicas": 1,
      "concurrency": 32,
      "image": ""
    },
    "triggers": [
      {
        "name": "deploymentJsonPlugin",
        "filter": {'annotated': true},
        "resource": "Item",
        "actions": [
          "Created"
        ],
        "active": true,
        "executionMode": "Once"
      }
    ],
    "config": {
      "message": "My first plugin with deployment.json"
    },
    "pluginRevision": "latest"
    }

In this case:
    - deployment name is: deployment
    - it is attached to plugin "deploymentJsonPlugin"
    - deployment will work on cpu and allow 32 procecces to run simultaneously
    - container autoscale limit is 1
    - plugin version is latest
    - a trigger by the name of deploymentJsonPlugin will be created and will trigger this deployment anytime an Item is created in the project.
    - no image was provided so default docker image will be used for this deployment


| Now we can deploy the plugin to the cloud(i.e: make a running instance out of it)

CLI

.. code-block:: python

   $ dlp plugins deploy

SDK

.. code-block:: python

   config = {
      "message": "My first plugin with deployment.json"
    }

   runtime = {
      "gpu": false,
      "replicas": 1,
      "concurrency": 32,
      "image": ""
    }

   # deploy plugin
   deployment = plugin.deployments.deploy(
                        deployment_name='deployment-json',
                        plugin=plugin,
                        config=config,
                        runtime=runtime)

    filters = dl.Filters()
    filters.add(field='annotated', values=True)

    # create trigger
    trigger = deployment.triggers.create(
                                    deployment_id=deployment.id,
                                    name='test_trigger',
                                    filters=filters,
                                    resource=dl.TriggerResource.ITEM,
                                    actions=dl.TriggerAction.CREATED,
                                    active=True,
                                    executionMode=dl.TriggerExecutionMode.ONCE)

Triggers
===========

Lets say we have a deployment (a plugin we have deployed).

If we want this deployment to be triggered automatically when something happens, we can do so by creating a trigger.

Triggers can work on items, datasets or annotations and be triggered upon creation, update or deletion.

Create a trigger:

.. code-block:: python

    import dtlpy as dl

    # get deployment
    deployment = dl.deployments.get(deployment_name="My deployment name")

    ######################################################################
    # create trigger for for when item is uploaded to directory "/train" #
    ######################################################################

    # create filter
    filters = dl.Filters()
    filters.add(field='dir', value='/train')

    # create trigger
    trigger = deployment.triggers.create(
        deployment_id=deployment.id,
        resource=dl.TriggerResource.ITEM,
        actions=dl.TriggerAction.CREATED',
        name='training-trigger',
        filters=filters,
        executionMode=dl.TriggerExecutionMode.ONCE
    )
