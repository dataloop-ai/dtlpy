Starting With Plugins
=====================

In this tutorial you will generate a basic plugin, modify it, and test it locally

Bootstraping the plugin
-----------------------

Create a local dataloop repository

.. code::

   $ dlp init

Checkout to a local project and dataset

.. code::

    $ dlp checkout project <project_name/project_id>
    $ dlp checkout dataset <dataset_name/dataset_id>


Create a Plugin from the current directory

.. code::

   $ dlp plugins generate

Developing the plugin
---------------------
| The plugin folder contains the following components:
| 1) A .dataloop folder containing the local state, you should not touch it.
| 2) A plugin.json file which defines the inputs and outputs of the plugin.
| 3) A mock.json file which defines sample entities to be used for the test command.
| 4) A src folder containing the code to be executed, the run method of main.py is the entry
|  point of the plugin.
|
| We currently support 4 types of entites: Dataset, Item, Annotation and a
| special Json entity for passing arbitrary jsons.
|
| The plugin.json file contains 2 fields:
| 1) An inputs field which contains an array of the entities that will be passed to src/main:run.
|  as named arguments
| 2) An outputs field which contains an array of the entities that will be returned from src/main:run
|  as a tuple.
|
| The mock.json file currently has only the field inputs which defines the inputs given to
| src/main:run when running **"dlp plugins test"**.
| The array in the mock.json file should correspond to the input field of the plugin.json file.

| The value of an annotation entity should be in the form:
| {
|   "dataset_id": <dataset_id>,
|   "item_id": <item_id>,
|   "annotation_id": <annotation_id>
| }
| And the values of dataset and item entities should look accordingly.
| The value of a Json entity can be any json.

Test the code locally
---------------------

| Once you have a mock.json specifying existing items/annotations in your checked out
| project and dataset, test the plugin locally with:

.. code::

   $ dlp plugins test

Deploy to cloud
---------------

To be continued...