Annotation Types
================

Using the annotations definitions classes you can create, edit, view and upload Platform annotations.
Supported types: Classification, Point, Ellipse, Box, Polyline, Polygon, Segmentation.

Each annotations init recieves the coordinates for the specific type, label and optional attributes.

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


Init a Platform annotations with the Definition for viewing and drawing:

.. code-block:: python

    import dtlpy as dl
    # Get source project and dataset
    project = dl.projects.get(project_name='FirstProject')
    dataset = project.datasets.get(dataset_name='FirstDataset')
    item = dataset.items.get(filepath='/image.jpg)

    builder = item.annotations.builder())
    builder.add(annotation_definition=dl.Segmentation(geo=mask,
                                                   label=label)
    # get annotations mask
    mask = builder.show()

    # draw on image
    image = builder.show(image)
