import shutil

import behave
import os
import dtlpy as dl


@behave.when(u'I download items annotations with "{ann_type}" to "{path}"')
def step_impl(context, ann_type, path):
    if context.item.height is None:
        context.item.height = 768
    if context.item.width is None:
        context.item.width = 1536
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    if ann_type == 'img_mask':
        context.item.annotations.download(
            filepath=path,
            img_filepath=context.item_path,
            annotation_format=ann_type,
            thickness=1
        )
    elif ann_type == 'default':
        context.item.annotations.download(
            filepath=path,
            thickness=1)
    else:
        context.item.annotations.download(
            filepath=path,
            annotation_format=ann_type,
            thickness=1)
    context.annotation_download_filepath = path


@behave.when(u'I download items annotations from item with "{ann_type}" to "{path}"')
def step_impl(context, ann_type, path):
    if context.item.height is None:
        context.item.height = 768
    if context.item.width is None:
        context.item.width = 1536
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    context.item = dl.items.get(item_id=context.item.id)
    context.item.download(
        local_path=path,
        annotation_options=ann_type,
        thickness=1
    )


@behave.given(u'There are no files in folder "{folder_path}"')
def step_impl(context, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    if os.path.isdir(folder_path):
        # on git there are no empty folder so only if the folder exists check that it is empty
        items = os.listdir(folder_path)
        for item in items:
            if item != 'folder_keeper':
                path = os.path.join(folder_path, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        dirs = os.listdir(folder_path)
        dirs.pop(dirs.index('folder_keeper'))
        assert len(dirs) == 0


@behave.then(u'Item annotation "{file_type}" has been downloaded to "{folder_path}"')
def step_impl(context, file_type, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    items = os.listdir(folder_path)
    if file_type == 'json':
        file = file_type + '.json'
    elif file_type == 'vtt':
        file = file_type + '.vtt'
    else:
        file = file_type + '.png'
    assert file in items


@behave.then(u'video Item annotation "{file_type}" has been downloaded to "{folder_path}"')
def step_impl(context, file_type, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    items = os.listdir(folder_path)
    if file_type == 'json':
        file = file_type + '.json'
    else:
        file = file_type + '.mp4'
    assert file in items


# @behave.then(u'"{file_type}" is correctly downloaded (compared with "{file_to_compare}")')
# def step_impl(context, file_type, file_to_compare):
#     path = 'downloaded_annotations'
#     path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
#     file_to_compare = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_to_compare)

#     file = file_type.lower() + '.png'
#     original = cv2.imread(file_to_compare)
#     downloaded = cv2.imread(os.path.join(path, file))
#     if original.shape == downloaded.shape:
#         difference = cv2.subtract(original, downloaded)
#         b, g, r = cv2.split(difference)
#         if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
#             assert True
#         else:
#             assert False
#     else:
#         assert False

@behave.then(u'I download the annotation to "{item_path}" with "{annotation_type}" type')
def step_impl(context, item_path, annotation_type):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.annotation_filepath = context.annotation_x_get.download(filepath=item_path,
                                                                    annotation_format=annotation_type)


@behave.then(u'annotation file exist in the path "{annotation_filepath}"')
def step_impl(context, annotation_filepath):
    files = os.listdir(os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotation_filepath))
    assert os.path.basename(context.annotation_filepath) in files


@behave.then(u'I download the items annotations with ViewAnnotationOptions "{file_type}" enum to find "{item_path}"')
def step_impl(context, file_type, item_path):
    folder_path = ""

    if file_type != "None":
        folder_path = os.path.dirname(os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path))

    if file_type == 'JSON':
        context.dataset.download_annotations(annotation_options=dl.ViewAnnotationOptions.JSON, local_path=folder_path)
        file = os.path.basename(item_path)
        items = os.path.join(folder_path, "json")
    elif file_type == 'VTT':
        context.dataset.download_annotations(annotation_options=dl.ViewAnnotationOptions.VTT, local_path=folder_path)
        file = os.path.basename(item_path)
        items = os.path.join(folder_path, "vtt")
    elif file_type == 'MASK':
        context.dataset.download_annotations(annotation_options=dl.ViewAnnotationOptions.MASK, local_path=folder_path)
        file = os.path.basename(item_path)
        items = os.path.join(folder_path, "mask")
    else:
        try:
            context.dataset.download_annotations(annotation_options=dl.ViewAnnotationOptions)
            assert False

        except Exception as e:
            assert folder_path in e.args[1]
            return  # END

    items = os.listdir(items)
    assert file in items


@behave.when(u'I download dataset annotations with "{ann_type}" to "{path}"')
def step_impl(context, ann_type, path):
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    context.dataset.download_annotations(
        local_path=path,
        annotation_options=ann_type,
    )


@behave.then(u'dataset "{folder_name}" folder has been downloaded to "{folder_path}"')
def step_impl(context, folder_name, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    items = os.listdir(folder_path)
    assert folder_name in items
    count_files = os.listdir(os.path.join(folder_path, folder_name))
    assert len(count_files) == 1


@behave.then(u'Validate annotation file has "{ann_count}" annotations')
def step_impl(context, ann_count):
    if not hasattr(context, 'annotation_download_filepath'):
        raise Exception(
            'annotation_download_filepath not found in context, please run: I download items annotations with "{ann_type}" to "{path}"')

    import json
    with open(context.annotation_download_filepath, 'r') as f:
        annotation_file = json.load(f)

    assert len(annotation_file['annotations']) == int(ann_count), f"TEST FAILED: expected {ann_count} annotations, got {len(annotation_file['annotations'])}"
