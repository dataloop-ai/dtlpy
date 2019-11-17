############
Similarity
############

Before we get started with Modality:

.. code-block:: python

    import dtlpy as dl

    project = dl.projects.get(project_name='my project')
    dataset = project.datasets.get(dataset_name='my dataset')

Lets create and upload a Similarity with the SDK
#################################################

.. code-block:: python

    # Get target item
    item = dataset.items.get(filepath='pink_sun.png')

    # Get item to compare
    item2 = dataset.items.get(filepath='black_moon.jpeg')

    # Create similarity
    similarity = dl.Similarity(ref=item.id, type=dl.SimilarityTypeEnum.ID, name='product similarity')

    # Add items to similarity
    similarity.add(ref=item2.id, type=dl.SimilarityTypeEnum.ID)

    # Add url to similarity
    url = 'http://www.sunset-in-chernobyl.jpg'
    similarity.add(ref=url, type=dl.SimilarityTypeEnum.URL)

    # Upload similarity
    dataset.items.upload(local_path=similarity, remote_path='/Chernobyl')
