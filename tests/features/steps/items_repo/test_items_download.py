import behave
import os
import shutil
import cv2


@behave.given(u'Folder "{folder_path}" is empty')
def step_impl(context, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    content = [name for name in os.listdir(folder_path)]
    if len(content) != 0:
        for item in content:
            path = os.path.join(folder_path, item)
            shutil.rmtree(path)
        content = [name for name in os.listdir(folder_path)]
    assert len(content) == 0


@behave.when(u'I download an item by the name of "{item_name}" to "{download_path}"')
def step_impl(context, item_name, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    context.dataset.items.download(filepath=item_name,
                                   item_id=None,
                                   save_locally=True,
                                   local_path=download_path,
                                   chunk_size=8192,
                                   download_options=None,
                                   download_item=True,
                                   annotation_options=None,
                                   verbose=True,
                                   show_progress=False)


@behave.then(u'There are "{item_count}" files in "{local_path}"')
def step_impl(context, item_count, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    content = [name for name in os.listdir(local_path)]
    assert len(content) == int(item_count)


@behave.then(u'Item is correctlly downloaded to "{downloaded_path}" (compared with "{item_to_compare}")')
def step_impl(context, downloaded_path, item_to_compare):
    downloaded_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], downloaded_path)
    item_to_compare = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_to_compare)

    original = cv2.imread(downloaded_path)
    downloaded = cv2.imread(item_to_compare)
    if original.shape == downloaded.shape:
        difference = cv2.subtract(original, downloaded)
        b, g, r = cv2.split(difference)
        if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
            assert True
        else:
            assert False
    else:
        assert False


@behave.when(u'I download an item by the id of "{item_name}" to "{download_path}"')
def step_impl(context, item_name, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    context.dataset.items.download(filepath=None,
                                   item_id=context.item.id,
                                   save_locally=True,
                                   local_path=download_path,
                                   chunk_size=8192,
                                   download_options=None,
                                   download_item=True,
                                   annotation_options=None,
                                   verbose=True,
                                   show_progress=False)


@behave.when(u'I download without saving an item by the id of "{item_name}"')
def step_impl(context, item_name):
    context.item_data = context.dataset.items.download(filepath=item_name,
                                                       item_id=context.item.id,
                                                       save_locally=False,
                                                       local_path=None,
                                                       chunk_size=8192,
                                                       download_options=None,
                                                       download_item=True,
                                                       annotation_options=None,
                                                       verbose=True,
                                                       show_progress=False)


@behave.then(u'I receive item data')
def step_impl(context):
    pass


@behave.when(u'I upload item data by name of "{item_name}"')
def step_impl(context, item_name):
    context.dataset.items.upload(filepath=context.item_data,
                                 annotations_filepath=None,
                                 remote_path=None,
                                 uploaded_filename=item_name,
                                 callback=None,
                                 upload_options=None)


@behave.then(u'Item uploaded from data equals initial item uploaded')
def step_impl(context):
    pass
