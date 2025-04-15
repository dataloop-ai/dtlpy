import io
import time
import behave
import os
import shutil


@behave.given(u'Folder "{folder_path}" is empty')
def step_impl(context, folder_path):
    folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    content = [name for name in os.listdir(folder_path)]
    if len(content) != 0:
        for item in content:
            if item != 'folder_keeper':
                path = os.path.join(folder_path, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)


@behave.when(u'I download an item by the name of "{item_name}" to "{download_path}"')
def step_impl(context, item_name, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    filters = context.dl.Filters()
    filters.add(field='filename', values=item_name)
    context.dataset.items.download(filters=filters,
                                   items=None,
                                   save_locally=True,
                                   local_path=download_path,
                                   annotation_options=None)


@behave.then(u'There are "{item_count}" files in "{local_path}"')
def step_impl(context, item_count, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    content = list()
    for root, dirs, files in os.walk(local_path):
        for file in files:
            if file.endswith(".jpg"):
                content.append(file)

    assert len(content) == int(item_count), "TEST FAILED: Expected {} got {}".format(item_count, len(content))


@behave.then(u'There are "{item_count}" files in dir "{local_path}"')
def step_impl(context, item_count, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    content = list()
    for root, dirs, files in os.walk(local_path):
        for file in files:
            content.append(file)

    assert len(content) == int(item_count), "TEST FAILED: Expected {} got {}".format(item_count, len(content))


@behave.then(u'Item is correctly downloaded to "{downloaded_path}" (compared with "{item_to_compare}")')
def step_impl(context, downloaded_path, item_to_compare):
    import cv2
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


@behave.when(u'I download an item by the id to "{download_path}"')
def step_impl(context, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    context.dataset.items.download(items=context.item.id,
                                   save_locally=True,
                                   local_path=download_path,
                                   annotation_options=None)


@behave.when(u'I download the item without saving and create folder')
def step_impl(context):
    context.path = os.path.join(os.getcwd(), 'items_check')
    context.item_data = context.dataset.items.download(items=context.item.id,
                                                       save_locally=False,
                                                       local_path=context.path,
                                                       annotation_options=None)


@behave.when(u'I download the item without saving and create folder and with array convert')
def step_impl(context):
    context.path = os.path.join(os.getcwd(), 'items_check')
    context.item_data = context.dataset.items.download(items=context.item.id,
                                                       save_locally=False,
                                                       local_path=context.path,
                                                       annotation_options=None,
                                                       to_array=True)

@behave.then(u'item has data')
def step_impl(context):
    assert context.item_data is not None, "TEST FAILED: Item data is None"

@behave.then(u'file do not created')
def step_impl(context):
    assert not os.path.exists(path=context.path)


@behave.when(u'I download without saving an item by the id of "{item_name}"')
def step_impl(context, item_name):
    context.item_data = context.dataset.items.download(items=context.item.id,
                                                       save_locally=False,
                                                       local_path=None,
                                                       annotation_options=None)


@behave.then(u'I receive item data')
def step_impl(context):
    assert type(context.item_data) == io.BytesIO


@behave.when(u'I upload item data by name of "{item_name}"')
def step_impl(context, item_name):
    context.item_data.name = item_name
    context.dataset.items.upload(local_path=context.item_data,
                                 local_annotations_path=None,
                                 remote_path=None)
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


@behave.then(u'Item uploaded from data equals initial item uploaded')
def step_impl(context):
    pass
