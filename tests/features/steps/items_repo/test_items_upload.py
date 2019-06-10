import behave
import os
import cv2
from dtlpy import entities


@behave.when(u'I upload a file in path "{item_local_path}"')
def step_impl(context, item_local_path):
    item_local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_local_path)
    context.item = context.dataset.items.upload(
        filepath=item_local_path,
        remote_path=None,
        uploaded_filename=None,
        callback=None,
        upload_options=None,
    )


@behave.when(u'I upload with "{option}" a file in path "{item_local_path}"')
def step_impl(context, item_local_path, option):
    item_local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_local_path)
    context.item = context.dataset.items.upload(
        filepath=item_local_path,
        remote_path=None,
        uploaded_filename=None,
        callback=None,
        upload_options=option,
    )


@behave.when(u'I upload file in path "{item_local_path}" to remote path "{remote_path}"')
def step_impl(context, item_local_path, remote_path):
    item_local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_local_path)
    context.item = context.dataset.items.upload(
        filepath=item_local_path,
        remote_path=remote_path,
        uploaded_filename=None,
        callback=None,
        upload_options=None,
    )


@behave.then(u'Item exist in host')
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)


@behave.then(u'Item object from host equals item uploaded')
def step_impl(context):
    item_get = context.item_get.to_json()
    item = context.item.to_json()
    item_get.pop('metadata')
    item.pop('metadata')
    assert item == item_get


@behave.then(u'Item in host equals item in "{item_local_path}"')
def step_impl(context, item_local_path):
    download_path = 'download_item/image/0000000162.jpg'
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    file_to_compare = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_local_path)

    context.dataset.items.download(filepath=None, item_id=context.item.id,
                                   save_locally=True, local_path=download_path,
                                   chunk_size=8192, download_options=None,
                                   download_item=True, annotation_options=None,
                                   verbose=True, show_progress=False)

    original = cv2.imread(file_to_compare)
    downloaded = cv2.imread(download_path)
    if original.shape == downloaded.shape:
        difference = cv2.subtract(original, downloaded)
        b, g, r = cv2.split(difference)
        if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
            assert True
        else:
            assert False
    else:
        assert False


@behave.then(u'Upload method returned an Item object')
def step_impl(context):
    assert type(context.item) == entities.Item


@behave.then(u'Item in host is in folder "{remote_path}"')
def step_impl(context, remote_path):
    assert remote_path in context.dataset.items.get(item_id=context.item.id).filename


@behave.when(u'I upload the file in path "{local_path}" with remote name "{remote_filename}"')
def step_impl(context, local_path, remote_filename):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    context.item = context.dataset.items.upload(
        filepath=local_path,
        remote_path=None,
        uploaded_filename=remote_filename,
        callback=None,
        upload_options=None,
    )


@behave.then(u'Item in host has name "{remote_name}"')
def step_impl(context, remote_name):
    assert remote_name in context.dataset.items.get(item_id=context.item.id).filename


@behave.then(u'Item was merged to host')
def step_impl(context):
    assert context.item_get.id == context.item.id


@behave.then(u'Item was overwrite to host')
def step_impl(context):
    assert context.item_get.id != context.item.id


@behave.when(u'I try to upload file in path "{local_path}" to remote path "{illegal_remote_path}"')
def step_impl(context, local_path, illegal_remote_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    try:
        context.item = context.dataset.items.upload(
            filepath=local_path,
            remote_path=illegal_remote_path,
            uploaded_filename=None,
            callback=None,
            upload_options=None,
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to upload file in path "{illegal_local_path}"')
def step_impl(context, illegal_local_path):
    illegal_local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], illegal_local_path)
    try:
        context.item = context.dataset.items.upload(
            filepath=illegal_local_path,
            remote_path=None,
            uploaded_filename=None,
            callback=None,
            upload_options=None,
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u'I download items to buffer')
def step_impl(context):
    items = context.dataset.items.get_all_items()
    context.buffer = context.dataset.items.download_batch(items=items,
                                                          save_locally=False,
                                                          local_path=None,
                                                          chunk_size=8192,
                                                          download_options=None,
                                                          download_item=True,
                                                          annotation_options=None,
                                                          verbose=True,
                                                          show_progress=False
                                                          )


@behave.given(u'I delete all items from host')
def step_impl(context):
    context.item_list = context.dataset.items.list()
    for item in context.item_list.items:
        if item.type != 'dir':
            context.dataset.items.delete(item_id=item.id)
    context.item_list = context.dataset.items.list()
    assert len(context.item_list.items) == 1


@behave.when(u'I upload items from buffer to host')
def step_impl(context):
    context.items_uploaded = 0
    for buff in context.buffer:
        uploaded_filename = "file" + str(context.items_uploaded) + '.jpg'
        context.items_uploaded += 1
        context.dataset.items.upload(
            buff,
            remote_path=None,
            uploaded_filename=uploaded_filename,
            callback=None,
            upload_options=None,
        )


@behave.then(u'There are "{item_count}" items in host')
def step_impl(context, item_count):
    context.item_list = context.dataset.items.list(query={"itemType": "file"})
    assert len(context.item_list.items) == int(item_count) == context.items_uploaded
