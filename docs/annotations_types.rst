Annotations
===========

Annotation Types
----------------
Using the annotations definitions classes you can create, edit, view and upload Platform annotations.
Supported types: Classification, Point, Ellipse, Box, Polyline, Polygon, Segmentation.

Each annotations init receives the coordinates for the specific type, label and optional attributes.

.. code-block:: python

    import dtlpy as dl

    # Init Classification with label (no coordinates)
    annotations_definition = dl.Classification(label=label)

    # Init Point with x,y coordinates:
    annotations_definition = dl.Point(x=x, y=y, label=label)

    # Init Ellipse with params for ellipse; x and y for the center, rx and ry for the radius and rotation angle:
    annotations_definition = dl.Ellipse(x=x, y=y, rx=rx, ry=ry, angle=angle, label=label)

    # Init Box with bounding box params:
    annotations_definition = dl.Box(top=top, left=left, bottom=bottom, right=right, label=label)

    # Init Polyline with array of points: [[x1,y1], [x2,y2], ..., [xn, yn]]
    annotations_definition = dl.Polyline(geo=geo, label=label)

    # Init Polygon same as Polyline (but it will close the polygon)
    annotations_definition = dl.Polygon(geo=geo, label=label)

    # Init Segmentation with a binary mask (0 for background, 1 for the annotations) same shape as the image:
    # np.zeros((img_shape)) for the background and color in 1 for the annotation
    annotations_definition = dl.Segmentation(geo=geo, label=label)


Upload and Show
---------------
Init a Platform annotations with the Definition for viewing and drawing:

.. code-block:: python

    import dtlpy as dl
    # Get source project and dataset
    project = dl.projects.get(project_name='FirstProject')
    dataset = project.datasets.get(dataset_name='FirstDataset')
    item = dataset.items.get(filepath='/image.jpg)

    builder = item.annotations.builder()
    builder.add(annotation_definition=dl.Segmentation(geo=mask,
                                                   label=label)
    # get annotations mask
    mask = builder.show()

    # draw on image
    image = builder.show(image)

    # upload annotations to item
    item.annotations.upload(annotations=builder)


Model Metadata
--------------
Add metadata to annotation when uploading.
This can be used to add "model" metadata to each annotations and filter by them in the platform

.. code-block:: python

    builder = item.annotations.builder()
    # add annotation with model name and confidence
    builder.add(annotation_definition=dl.Box(top=10, left=10, bottom=100, right=100,
                                             label=label),
                metadata={'user': {'model': {'name': 'model_name',
                                             'confidence': 0.9}}})
    # upload annotations to item
    item.annotations.upload(annotations=builder)

Parenting Annotations
---------------------
You can set annotations relation using the parent_id input:

.. code-block:: python

    #############################
    # when creating annotations #
    #############################
    builder = item.annotations.builder()
    builder.add(annotation_definition=dl.Box(top=10, left=10, bottom=100, right=100,
                                             label='parent'))
    # upload parent annotation
    annotations = item.annotations.upload(annotations=builder)

    # create the child annotation
    builder = item.annotations.builder()
    builder.add(annotation_definition=dl.Box(top=50, left=50, bottom=150, right=150,
                                             label='child'),
                parent_id=annotations[0].id)
    # upload annotations to item
    item.annotations.upload(annotations=builder)

    ###########################
    # on existing annotations #
    ###########################
    # create and upload parent annotation
    builder = item.annotations.builder()
    builder.add(annotation_definition=dl.Box(top=10, left=10, bottom=100, right=100,
                                             label='parent'))
    parent_annotation = item.annotations.upload(annotations=builder)[0]
    # create and upload child annotation
    builder = item.annotations.builder()
    builder.add(annotation_definition=dl.Box(top=50, left=50, bottom=150, right=150,
                                             label='child'))
    child_annotation = item.annotations.upload(annotations=builder)[0]

    # set the child parent ID to the parent
    child_annotation.parent_id = parent_annotation.id
    # update the annotation
    child_annotation.update(system_metadata=True)

