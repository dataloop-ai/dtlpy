import behave
import json
import os


@behave.when(u'I upload annotations from file: "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    with open(file_path, "r") as f:
        context.annotations = json.load(f)["annotations"]
    context.item.annotations.upload(context.annotations)


@behave.then(u"Item should have annotations uploaded")
def step_impl(context):
    annotations_list = context.item.annotations.list()
    for annotation in annotations_list:
        ann = {
            "type": annotation.type,
            "label": annotation.label,
            "attributes": annotation.attributes,
            "coordinates": annotation.coordinates,
        }
        assert ann in context.annotations


@behave.given(u"There is an annotation description")
def step_impl(context):
    context.annotation_description = {
        "type": "box",
        "label": "car",
        "attributes": ["Occlusion2"],
        "coordinates": [
            {"x": 700, "y": 200},
            {"x": 800, "y": 250},
        ],
    }


@behave.when(u"I upload annotation description to Item")
def step_impl(context):
    context.item.annotations.upload(context.annotation_description)


@behave.then(u"Item should have annotation uploaded")
def step_impl(context):
    annotation = context.item.annotations.list()[0]
    ann = {
        "type": annotation.type,
        "label": annotation.label,
        "attributes": annotation.attributes,
        "coordinates": annotation.coordinates,
    }
    assert ann == context.annotation_description


@behave.given(u'There is an illegal annotation description')
def step_impl(context):
    context.annotation_description = {
        "type": "box",
        "label": "car",
        "attributes": ["Occlusion2"]
    }


@behave.when(u'I try to upload annotation description to Item')
def step_impl(context):
    try:
        context.item.annotations.upload(context.annotation_description)
        context.error = None
    except Exception as e:
        context.error = e
