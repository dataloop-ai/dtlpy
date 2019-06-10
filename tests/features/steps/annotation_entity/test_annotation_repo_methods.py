import behave
import os
import cv2


@behave.when(u"I delete entity annotation x")
def step_impl(context):
    context.annotation_x.delete()


@behave.when(u'I download Entity annotation x with mask and instance to "{img_filepath}"')
def step_impl(context, img_filepath):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], img_filepath)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    img_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], '0000000162.jpg')
    img = cv2.imread(img_path)
    dimensions = img.shape
    img_shape = (dimensions[1], dimensions[0])
    context.annotation_x.download(
        filepath=path,
        get_mask=True,
        get_instance=True,
        img_shape=img_shape,
        thickness=1,
    )


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


@behave.then(u"Item in host have annotation uploaded")
def step_impl(context):
    context.annotation.upload()
    host_annotation = context.item.annotations.list()[0]
    assert host_annotation.label == context.annotation.label
    assert host_annotation.type == context.annotation.type
