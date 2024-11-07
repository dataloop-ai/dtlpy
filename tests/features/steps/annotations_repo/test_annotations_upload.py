import behave
import json
import os


@behave.when(u'I upload annotations from file: "{file_path}" with merge "{merge_ann}"')
def step_impl(context, file_path, merge_ann):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    merge_ann = True if merge_ann == 'True' else False
    with open(file_path, "r") as f:
        context.annotations = json.load(f)["annotations"]
    context.item.annotations.upload(context.annotations, merge=merge_ann)


@behave.when(u'I save binary annotation coordinates')
def step_impl(context):
    context.item = context.project.items.get(item_id=context.item.id)
    annotations = context.item.annotations.list()
    for annotation in annotations:
        if annotation.type == 'binary':
            context.binary_annotation = annotation

@behave.then(u'binary annotation has been merged')
def step_impl(context):
    context.item = context.project.items.get(item_id=context.item.id)
    annotations = context.item.annotations.list()
    for annotation in annotations:
        if annotation.type == 'binary':
            assert annotation.coordinates != context.binary_annotation.coordinates, 'Binary annotation has not been merged'
            assert annotation.id == context.binary_annotation.id, 'Binary annotation has not been merged'
            assert annotation.label == context.binary_annotation.label, 'Binary annotation has not been merged'
            break

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
        # remove 'z' value to match file
        if annotation.type != 'gis':
            for coordinate in ann['coordinates']:
                coordinate.pop('z')
        assert ann in context.annotations

@behave.then(u"Item should have all gis annotation types uploaded")
def step_impl(context):
    expected_annotations_types = ['point', 'polyline', 'polygon', 'box']
    annotations_list = context.item.annotations.list()
    for annotation in annotations_list:
        assert annotation.type == 'gis'
        assert isinstance(annotation.annotation_definition, context.dl.Gis)
        expected_annotations_types.remove(annotation.coordinates['geo_type'])
    assert len(expected_annotations_types) == 0



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
    # remove 'z' value to match file
    for coordinate in ann['coordinates']:
        coordinate.pop('z')
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
