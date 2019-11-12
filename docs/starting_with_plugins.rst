Starting With Plugins
=====================

In this tutorial you will generate a basic plugin, modify it, and test it locally

Bootstraping the plugin
-----------------------
Before starting run

Checkout to a local project and dataset

.. code-block:: python

    $ dlp projects checkout <project_name/project_id>
    $ dlp datasets checkout <dataset_name/dataset_id>


Create a Plugin at the current directory

.. code-block:: python

   $ dlp plugins generate --plugin-name


The above command should generate the following files in the current working directory:

1. plugin.json
2. main.py
3. mock.json
4. deployment.json
5. .gitignore

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

In this case, the plugin name is: myPlugin and it expects an item input.
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

The value of a Json entity can be any json.

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
            assert isinstance(progress, dl.Progress)
            progress.update(status='inProgress', progress=0)
            item.metadata['message']['user']['firstPlugin'] = self.message
            item.update()
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

| In this case, the init will set global attribute 'message' and the session will add this
| message to the item's metadata.

| Run method receives a progress object which allows us to update session progress.

| DO NOT MAKE CHANGES TO THE main.py LAYOUT!
| Changes we are allowed to make are:
| 1. run() params (as long as it still receive progress and inputs defined in plugin.json).
| 2. Code within run and init methods.
| 3. Addition of other methods and classes
| 4. Additional imports

Testing Plugin
---------------------

Your mock.json exists in-order to allow local plugin tests.
By providing plugin inputs in the "input" field of mock.json
And providing init params in the "config" field of mock.json
You can perform:

.. code-block:: python

   $ dlp plugins test

This will run the init method followed by the run method with params provided in the mock.json.

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

Deploy to cloud
=====================
First push the pluging by performing:

.. code-block:: python

   $ dlp plugins push

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
        "filter": {},
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


| Now we can deploy the plugin to the cloud(i.e: make a running instance out of it)

.. code-block:: python

   $ dlp plugins deploy


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
        resource='Item',
        actions='Created',
        name='training-trigger',
        filters=filters
    )
