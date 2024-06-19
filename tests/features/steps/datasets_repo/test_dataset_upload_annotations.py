import time
import behave
import os
import json


@behave.then(u'I upload annotations to dataset')
def step_impl(context):
    json_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "upload_dataset_annotations")
    context.dataset.upload_annotations(local_path=json_file_path, clean=True)


@behave.then(u'Annotations in item equal to the annotations uploaded')
def step_impl(context):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "upload_dataset_annotations/0000000162.json")
    with open(file_path) as json_file:
        annotations_uploaded = json.load(json_file)
    annotations_uploaded = annotations_uploaded['annotations']
    item_annotations = context.item.annotations.list().annotations
    assert len(annotations_uploaded) == len(item_annotations)
    for annotation in item_annotations:
        annotation_json = annotation.to_json()
        ann = {'attributes': annotation_json['attributes'],
               'coordinates': annotation_json['coordinates'],
               'label': annotation_json['label'],
               'type': annotation_json['type']}
        assert ann in annotations_uploaded


@behave.when(u'Item in path "{item_path}" is uploaded to "Dataset" in remote path "{remote_path}"')
def step_impl(context, item_path, remote_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path, remote_path=remote_path)

    # wait for platform attributes
    limit = 10 * 30
    stat = time.time()
    while True:
        time.sleep(3)
        context.item = context.dataset.items.get(item_id=context.item.id)
        if "video" in context.item.mimetype:
            if context.item.fps is not None:
                break
        elif context.item.mimetype is not None:
            break
        if time.time() - stat > limit:
            raise TimeoutError("Timeout while waiting for platform attributes")

    context.item = context.dataset.items.get(item_id=context.item.id)
    if context.item.name.endswith('.mp4') and context.item.fps is None:
        context.item.fps = 25
    if context.item.name.endswith('.jpg') or context.item.name.endswith('.png'):
        if context.item.height is None:
            context.item.height = 768
        if context.item.width is None:
            context.item.width = 1536


@behave.then(u'I upload annotations to dataset in new end point "{remote_root_path}"')
def step_impl(context, remote_root_path):
    json_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "upload_dataset_annotations")
    context.dataset.upload_annotations(local_path=json_file_path, clean=True, remote_root_path=remote_root_path)
