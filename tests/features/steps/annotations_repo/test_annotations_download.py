import behave
import os
import cv2


@behave.when(u'I download items annotations with mask to "{path}"')
def step_impl(context, path):
    if context.item.height is None:
        context.item.height = 768
    if context.item.width is None:
        context.item.width = 1536
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    context.item.annotations.download(
        filepath=path,
        annotation_format='mask',
        thickness=1
    )


@behave.when(u'I download items annotations with instance to "{path}"')
def step_impl(context, path):
    if context.item.height is None:
        context.item.height = 768
    if context.item.width is None:
        context.item.width = 1536
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    context.item.annotations.download(
        filepath=path,
        annotation_format='instance',
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
                os.remove(path)
        dirs = os.listdir(folder_path)
        dirs.pop(dirs.index('folder_keeper'))
        assert len(dirs) == 0


@behave.then(u'Item annotation "{file_type}" has been downloaded to "{folder_path}"')
def step_impl(context, file_type, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    items = os.listdir(folder_path)
    file = file_type + '.png'
    assert file in items


# @behave.then(u'"{file_type}" is correctlly downloaded (compared with "{file_to_compare}")')
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
