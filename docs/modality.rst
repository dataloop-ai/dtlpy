############
Modality
############

Modality allows adding multiple items and toggling between them when annotating. These are typically images from multiple sensors that are overlaid. Items loaded as a modality will load together when source image is loaded.

Before we get started with Modality:

.. code-block:: python

    import dtlpy as dl

    project = dl.projects.get(project_name='my project')
    dataset = project.datasets.get(dataset_name='my dataset')

Adding modality to item
########################

Lets say I have 2 items:

.. code-block:: python

    # First item
    item1 = dataset.items.get(item_id='')

    # Second item
    item2 = dataset.items.get(item_id='')

If I want to add second item as modality to the first item

.. code-block:: python

    # create modality
    item1.modalities.create(name='my modality', modality_type=dl.ModalityTypeEnum.OVERLAY, ref=item2.id)

    # Update item to apply changes to platform
    item1.update()

Upload items and modalities using threads
#########################################
For more examples go to :doc:`examples.`.

