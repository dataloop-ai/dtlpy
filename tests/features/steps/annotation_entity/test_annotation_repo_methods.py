import behave
import os
import random


@behave.when(u"I delete entity annotation x")
def step_impl(context):
    context.annotation_x.delete()


@behave.when(u'I download Entity annotation x with "{annotation_format}" to "{img_filepath}"')
def step_impl(context, img_filepath, annotation_format):
    import cv2
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], img_filepath)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    img_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], '0000000162.jpg')
    img = cv2.imread(img_path)
    dimensions = img.shape
    height = dimensions[0]
    width = dimensions[1]
    context.annotation_x.download(
        filepath=path,
        annotation_format=annotation_format,
        height=height,
        width=width,
        thickness=1,
        with_text=False)


@behave.given(u'I change annotation x label to "{new_label}"')
def step_impl(context, new_label):
    context.annotation_x.label = new_label


@behave.given(u'I add field "{new_field}" to annotation x system metadata')
def step_impl(context, new_field):
    context.annotation_x.metadata = dict()
    context.annotation_x.metadata["system"] = new_field


@behave.when(u"I update annotation entity")
def step_impl(context):
    context.annotation_x.update(system_metadata=True)


@behave.then(u'Annotation x in host has label "{new_label}"')
def step_impl(context, new_label):
    assert context.annotation_get.label == new_label


# @behave.then(u'Annotation x in host has field "{new_field}" in system metadata')
# def step_impl(context, new_field):
#     assert new_field in context.annotation_get.metadata['system']


@behave.when(u"I get annotation x from host")
def step_impl(context):
    context.annotation_get = context.item.annotations.get(
        annotation_id=context.annotation_x.id
    )


@behave.when(u"I upload annotation")
def step_impl(context):
    annotation = {
        "type": "box",
        "label": "car",
        "attributes": ["Occlusion2"],
        "coordinates": [
            {"x": 714.086399, "y": 194.834737},
            {"x": 812.802021, "y": 243.433196},
        ]
    }
    context.item.annotations.upload(annotations=annotation)
    context.annotation = context.item.annotations.list()[0]
    context.item.annotations.delete(context.annotation)
    assert len(context.item.annotations.list()) == 0


@behave.when(u"I upload random x annotations")
def step_impl(context):
    annotation = {
        "type": "box",
        "label": "car",
        "attributes": ["Occlusion2"],
        "coordinates": [
            {"x": random.randrange(0, 500), "y": random.randrange(0, 500)},
            {"x": random.randrange(0, 500), "y": random.randrange(0, 500)},
        ]
    }
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    context.annotation_count = random.randrange(1, len(context.dataset.items.list()))

    itemList = context.dataset.items.list().items
    for i in range(context.annotation_count):
        context.item = itemList[i]
        context.item.annotations.upload(annotations=annotation)


@behave.then(u"analytic should say I have x annotations")
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    assert (context.annotation_count == context.dataset.annotated)


@behave.then(u"Item in host have annotation uploaded")
def step_impl(context):
    context.annotation.upload()
    host_annotation = context.item.annotations.list()[0]
    assert host_annotation.label == context.annotation.label
    assert host_annotation.type == context.annotation.type


@behave.given(u'I create an annotation')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    labels = context.dataset.labels
    context.annotation_point = context.dl.Annotation.new(item=context.item,
                                                         annotation_definition=context.dl.Point(x=100, y=150,
                                                                                                label=labels[0].tag,
                                                                                                attributes=['attr1']))
    context.annotation_box = context.dl.Annotation.new(item=context.item,
                                                       annotation_definition=context.dl.Box(left=100, top=200,
                                                                                            right=140, bottom=120,
                                                                                            label=labels[1].tag))
    context.annotation_ellipse = context.dl.Annotation.new(item=context.item,
                                                           annotation_definition=context.dl.Ellipse(x=300, y=300,
                                                                                                    angle=50, ry=20,
                                                                                                    rx=10,
                                                                                                    label=labels[2].tag,
                                                                                                    attributes=[
                                                                                                        'attr2']))
    context.annotation_polygon = context.dl.Annotation.new(item=context.item, annotation_definition=context.dl.Polygon(
        geo=[(300, 300), (320, 200), (350, 400), (300, 300)], label=labels[0].tag))
    context.num_annotations = 4


@behave.when(u'I upload annotation entity to item')
def step_impl(context):
    context.annotation_point.upload()
    context.annotation_box.upload()
    context.annotation_ellipse.upload()
    context.annotation_polygon.upload()


@behave.then(u'Item in host has annotation entity created')
def step_impl(context):
    annotations = context.item.annotations.list()
    assert len(annotations) == context.num_annotations, 'Missing annotation: uploaded: {}, found on item: {}'.format(
        len(annotations), context.num_annotations)
    for ann in annotations:
        if ann.type == 'box':
            assert context.annotation_box.label == ann.label
            # TODO
            # assert context.annotation_box.coordinates == ann.coordinates
            assert context.annotation_box.attributes == ann.attributes
        if ann.type == 'point':
            assert context.annotation_point.label == ann.label
            assert context.annotation_point.coordinates == ann.coordinates
            assert context.annotation_point.attributes == ann.attributes
        if ann.type == 'ellipse':
            assert context.annotation_ellipse.label == ann.label
            assert context.annotation_ellipse.coordinates == ann.coordinates
            assert context.annotation_ellipse.attributes == ann.attributes
        if ann.type == 'segment':
            assert context.annotation_polygon.label == ann.label
            assert context.annotation_polygon.coordinates == ann.coordinates
            assert context.annotation_polygon.attributes == ann.attributes


@behave.given(u'I create a video annotation')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    labels = context.dataset.labels
    x = 200
    y = 200
    context.annotation = context.dl.Annotation.new(item=context.item,
                                                   annotation_definition=context.dl.Point(x=200, y=200,
                                                                                          label=labels[1].tag))
    ann = context.annotation
    for i in range(300):
        context.annotation.add_frame(annotation_definition=context.dl.Point(x=x + i,
                                                                            y=y + i,
                                                                            label=ann.label))


@behave.when(u'I upload video annotation entity to item')
def step_impl(context):
    context.annotation.upload()


@behave.then(u'Item in host has video annotation entity created')
def step_impl(context):
    context.item = context.item.update()
    annotation = context.item.annotations.list()[0]
    if 'coordinateVersion' in annotation.metadata.get('system', {}) and \
            'coordinateVersion' not in context.annotation.metadata.get('system', {}):
        annotation.metadata['system'].pop('coordinateVersion')
    assert annotation.to_json()['metadata'] == context.annotation.to_json()['metadata']
    assert annotation.type == context.annotation.type
    assert annotation.label == context.annotation.label


@behave.when(u'I create video annotation by frames')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    labels = context.dataset.labels
    x = 200
    y = 200
    context.annotation = context.dl.Annotation.new(item=context.item)
    for i_frame in range(20):
        context.annotation.add_frame(annotation_definition=context.dl.Point(x=x, y=y, label=labels[1].tag),
                                     frame_num=i_frame,
                                     fixed=False)
    context.annotation = context.annotation.upload()


@behave.when(u'I add same frames to video annotation')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)
    labels = context.dataset.labels
    x = 200
    y = 200
    for i_frame in range(20, 40):
        context.annotation.add_frame(annotation_definition=context.dl.Point(x=x, y=y, label=labels[1].tag),
                                     frame_num=i_frame,
                                     fixed=False)
    context.annotation.update(True)


@behave.then(u'annotation do not have snapshots')
def step_impl(context):
    assert context.annotation.metadata['system']['snapshots_'] == [], 'Snapshots should be empty'
    assert context.annotation.to_json()['metadata']['system']['snapshots_'] == [], 'Snapshots should be empty'
