import behave
import random as r
import time


@behave.given(u"I get item annotation collection")
def step_impl(context):
    context.annotation_collection = context.item.annotations.list()


@behave.given(u'I change all annotations label to "{label}"')
def step_impl(context, label):
    for ann in context.annotation_collection:
        for i_frame, frame in ann.frames.items():
            ann.set_frame(i_frame)
            ann.label = label


@behave.given(u'I change all image annotations label to "{label}"')
def step_impl(context, label):
    for ann in context.annotation_collection:
        ann.label = label


@behave.when(u"I update annotation collection")
def step_impl(context):
    context.annotation_collection.update()
    time.sleep(7)


@behave.then(u'Annotations in host have label "{label}"')
def step_impl(context, label):
    context.annotation_collection = context.item.annotations.list()
    for ann in context.annotation_collection:
        for i_frame, frame in ann.frames.items():
            ann.set_frame(i_frame)
            assert ann.label == label


@behave.then(u'Image annotations in host have label "{label}"')
def step_impl(context, label):
    context.annotation_collection = context.item.annotations.list()
    for ann in context.annotation_collection:
        assert ann.label == label


@behave.when(u"I delete annotation collection")
def step_impl(context):
    context.annotation_collection.delete()


@behave.then(u"Item in host has no annotations")
def step_impl(context):
    context.annotation_collection = context.item.annotations.list()
    assert len(context.annotation_collection) == 0


@behave.given(u"I create item annotation collection")
def step_impl(context):
    context.annotation_collection = context.item.annotations.list()


@behave.then(u'"{num}" annotations are upload')
def step_impl(context, num):
    num_ann = int(num)
    assert len(context.item.annotations.list().annotations) == num_ann, "Number of annotations is not as expected"


@behave.when(u"I add a gis annotations to item")
def step_impl(context):
    box = context.dl.Gis(
        annotation_type=context.dl.GisType.BOX,
        geo=[
            [
                [
                    -118.33545020696846,
                    33.82643304226775
                ],
                [
                    -118.33544677833854,
                    33.82643304226775
                ],
                [
                    -118.33544677833854,
                    33.826421352507026
                ],
                [
                    -118.33545020696846,
                    33.826421352507026
                ],
                [
                    -118.33545020696846,
                    33.82643304226775
                ]
            ]
        ], label='car')

    polyline = context.dl.Gis(
        annotation_type=context.dl.GisType.POLYLINE,
        geo=[
            [
                -118.33542547032158,
                33.82643633447882
            ],
            [
                -118.33540897336161,
                33.82643356752507
            ],
            [
                -118.33540897005454,
                33.82642871822452
            ],
            [
                -118.33541921967488,
                33.826426863335726
            ],
            [
                -118.33542344940071,
                33.826436077343644
            ],
            [
                -118.33542639231051,
                33.82643044674003
            ],
            [
                -118.33541932625792,
                33.8264323433901
            ],
            [
                -118.33542031749415,
                33.82644421336565
            ],
            [
                -118.33542236477875,
                33.82643168077253
            ]
        ], label='car')
    point = context.dl.Gis(
        annotation_type=context.dl.GisType.POINT,
        geo=[
            -118.33540793707832,
            33.82642046242373
        ],
        label='car', )

    polygon = context.dl.Gis(
        annotation_type=context.dl.GisType.POLYGON,
        geo=[
            [
                [
                    -118.33543603201835,
                    33.82641747569975
                ],
                [
                    -118.33541563389792,
                    33.82641375053887
                ],
                [
                    -118.33542170322828,
                    33.82639922240139
                ],
                [
                    -118.33544032988657,
                    33.8264016410096
                ]
            ]
        ], label='car'
    )

    builder = context.item.annotations.builder()
    builder.add(annotation_definition=box)
    builder.add(annotation_definition=point)
    builder.add(annotation_definition=polyline)
    builder.add(annotation_definition=polygon)
    context.item.annotations.upload(annotations=builder)


@behave.given(u"I add a few annotations to image")
def step_impl(context):
    context.dataset = context.dataset.update()
    context.item = context.item.update()
    labels = context.dataset.labels
    height = context.item.height
    width = context.item.width
    if height is None:
        height = 768
    if width is None:
        width = 1536

    # point
    annotation_definition = context.dl.Point(
        x=r.randrange(0, width),
        y=r.randrange(0, height),
        label=r.choice(labels).tag,
        attributes={"1": "attr1"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)
    # box
    top = r.randrange(0, height)
    left = r.randrange(0, width)
    right = left + 100
    bottom = top + 100
    annotation_definition = context.dl.Box(
        top=top,
        left=left,
        right=right,
        bottom=bottom,
        label=r.choice(labels).tag,
        attributes={"1": "attr1", "2": "attr2"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)
    # poliygon
    geo = [
        (r.randrange(0, width), r.randrange(0, height)),
        (r.randrange(0, width), r.randrange(0, height)),
        (r.randrange(0, width), r.randrange(0, height)),
        (r.randrange(0, width), r.randrange(0, height)),
        (r.randrange(0, width), r.randrange(0, height)),
        (r.randrange(0, width), r.randrange(0, height)),
    ]
    annotation_definition = context.dl.Polygon(
        geo=geo, label=r.choice(labels).tag, attributes={"1": "attr1", "2": "attr2"}
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)
    # ellipse
    annotation_definition = context.dl.Ellipse(
        x=r.randrange(0, width),
        y=r.randrange(0, height),
        rx=r.randrange(0, 20),
        ry=r.randrange(0, 20),
        angle=r.randrange(0, 100),
        label=r.choice(labels).tag,
        attributes={"2": "attr2"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)


@behave.when(u"I upload annotation collection")
def step_impl(context):
    context.annotation_collection.upload()


@behave.then(u"Annotations in host equal annotations uploaded")
def step_impl(context):
    context.annotation_collection_get = context.item.annotations.list()
    assert len(context.annotation_collection_get) == len(context.annotation_collection)
    for ann_get in context.annotation_collection_get:
        for ann in context.annotation_collection:
            if ann.type == ann_get.type:
                break
        assert ann.label == ann_get.label
        assert ann.attributes == ann_get.attributes
        assert ann.coordinates == ann_get.coordinates


@behave.given(u"I add a few annotations to video")
def step_impl(context):
    context.dataset = context.dataset.update()
    context.item = context.item.update()
    labels = context.dataset.labels
    height = 1088
    width = 1920

    # point
    annotation_definition = context.dl.Point(
        x=r.randrange(0, width),
        y=r.randrange(0, height),
        label=r.choice(labels).tag,
        attributes={"1": "attr1"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)
    # box
    top = r.randrange(0, height)
    left = r.randrange(0, width)
    right = left + 100
    bottom = top + 100
    annotation_definition = context.dl.Box(
        top=top,
        left=left,
        right=right,
        bottom=bottom,
        label=r.choice(labels).tag,
        attributes={"1": "attr1", "2": "attr2"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)
    # ellipse
    annotation_definition = context.dl.Ellipse(
        x=r.randrange(0, width),
        y=r.randrange(0, height),
        rx=20,
        ry=10,
        angle=r.randrange(0, 100),
        label=r.choice(labels).tag,
        attributes={"2": "attr2"},
    )
    context.annotation_collection.add(annotation_definition=annotation_definition)


@behave.given(u"I add a few frames to annotations")
def step_impl(context):
    for ann in context.annotation_collection:
        for i in range(20):
            if ann.type == "box":
                top = ann.top + (i * 10)
                left = ann.left + (i * 10)
                right = ann.right + (i * 10)
                bottom = ann.bottom + (i * 10)
                annotation_definition = context.dl.Box(
                    top=top,
                    left=left,
                    right=right,
                    bottom=bottom,
                    label=ann.label,
                    attributes=ann.attributes,
                )
            elif ann.type == "point":
                x = ann.x + (i * 10)
                y = ann.y + (i * 10)
                annotation_definition = context.dl.Point(
                    x=x, y=y, label=ann.label, attributes=ann.attributes
                )
            elif ann.type == "ellipse":
                x = ann.x + (i * 10)
                y = ann.y + (i * 10)
                rx = ann.rx
                ry = ann.ry
                angle = ann.angle
                annotation_definition = context.dl.Ellipse(
                    x=x,
                    y=y,
                    rx=rx,
                    ry=ry,
                    angle=angle,
                    label=ann.label,
                    attributes=ann.attributes,
                )
            ann.add_frame(annotation_definition=annotation_definition, frame_num=i * 10)
