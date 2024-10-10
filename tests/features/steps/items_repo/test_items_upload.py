import behave
import os
import time
import shutil
import io


@behave.when(u'I upload a file in path "{item_local_path}"')
def step_impl(context, item_local_path):
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], item_local_path)
    context.item = context.dataset.items.upload(local_path=item_local_path,
                                                remote_path=None
                                                )


@behave.when(u'I upload with "{option}" a file in path "{item_local_path}"')
def step_impl(context, item_local_path, option):
    if option == 'overwrite':
        overwrite = True
    else:
        overwrite = False
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], item_local_path)
    context.item = context.dataset.items.upload(local_path=item_local_path,
                                                remote_path=None,
                                                overwrite=overwrite
                                                )


@behave.when(u'I upload file in path "{item_local_path}" to remote path "{remote_path}"')
def step_impl(context, item_local_path, remote_path):
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], item_local_path)
    context.item = context.dataset.items.upload(local_path=item_local_path,
                                                remote_path=remote_path)
    context.uploaded_item_with_trigger = context.item


@behave.then(u"Item exist in host")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)


@behave.then(u"Item object from host equals item uploaded")
def step_impl(context):
    item_get = context.item_get.to_json()
    item = context.item.to_json()
    item_get.pop("metadata")
    item.pop("metadata")
    assert item == item_get


@behave.then(u'Item in host when downloaded to "{download_path}" equals item in "{item_local_path}"')
def step_impl(context, item_local_path, download_path):
    import cv2
    download_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], download_path)
    file_to_compare = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], item_local_path)

    context.dataset.items.download(
        filters=None,
        items=context.item.id,
        local_path=download_path,
        file_types=None,
        save_locally=True,
        annotation_options=None,
        to_items_folder=False,
    )
    time.sleep(2)
    original = cv2.imread(file_to_compare)
    download_path = os.path.join(download_path, context.item.filename[1:])
    downloaded = cv2.imread(download_path)
    if original.shape == downloaded.shape:
        difference = cv2.subtract(original, downloaded)
        b, g, r = cv2.split(difference)
        if (
                cv2.countNonZero(b) == 0
                and cv2.countNonZero(g) == 0
                and cv2.countNonZero(r) == 0
        ):
            assert True
        else:
            assert False
    else:
        assert False
    if len(context.item.filename.split('/')) > 2:
        shutil.rmtree(os.path.split(download_path)[0])
    else:
        os.remove(download_path)


@behave.then(u"Upload method returned an Item object")
def step_impl(context):
    assert type(context.item) == context.dl.entities.Item


@behave.then(u'Item in host is in folder "{remote_path}"')
def step_impl(context, remote_path):
    assert remote_path in context.dataset.items.get(item_id=context.item.id).filename


@behave.when(u'I upload the file in path "{local_path}", opened as a buffer, with remote name "{remote_name}"')
def step_impl(context, local_path, remote_name):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    with open(local_path, "rb") as f:
        buffer = io.BytesIO(f.read())

    context.item = context.dataset.items.upload(
        local_path=buffer, remote_path=None, remote_name=remote_name
    )


@behave.when(u'I upload file in path "{local_path}" with remote name "{remote_name}" set via the buffer interface')
def step_impl(context, local_path, remote_name):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    with open(local_path, "rb") as f:
        buffer = io.BytesIO(f.read())
        buffer.name = remote_name

    context.item = context.dataset.items.upload(
        local_path=buffer, remote_path=None
    )


@behave.when(u'I upload the file in path "{local_path}" with remote name "{remote_name}"')
def step_impl(context, local_path, remote_name):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    context.item = context.dataset.items.upload(
        local_path=local_path, remote_path=None, remote_name=remote_name
    )


@behave.when(u'I upload the file in path "{local_path}" with description "{description}"')
def step_impl(context, local_path, description):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    context.item = context.dataset.items.upload(
        local_path=local_path, remote_path=None, item_description=description
    )


@behave.when(
    u'I upload the file from path "{local_path}" with remote name "{remote_name}" to remote path "{remote_path}"')
def step_impl(context, local_path, remote_path, remote_name):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    context.item = context.dataset.items.upload(
        local_path=local_path, remote_path=remote_path, remote_name=remote_name
    )


@behave.then(u'Item in host has name "{remote_name}"')
def step_impl(context, remote_name):
    assert remote_name in context.dataset.items.get(item_id=context.item.id).filename


@behave.then(u"Item was merged to host")
def step_impl(context):
    assert context.item_get.id == context.item.id


@behave.then(u"Item was overwrite to host")
def step_impl(context):
    assert context.item_get.id != context.item.id


@behave.when(u'I try to upload file in path "{local_path}" to remote path "{illegal_remote_path}"')
def step_impl(context, local_path, illegal_remote_path):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)
    # count error logs before
    context.error_logs_before = sum([1 for filename in os.listdir(os.getcwd()) if filename.startswith("log_")])
    # upload
    context.item = context.dataset.items.upload(local_path=local_path,
                                                remote_path=illegal_remote_path)
    # count error logs after
    context.error_logs_after = sum([1 for filename in os.listdir(os.getcwd()) if filename.startswith("log_")])


@behave.when(u'I try to upload file in path "{illegal_local_path}"')
def step_impl(context, illegal_local_path):
    illegal_local_path = os.path.join(
        os.environ["DATALOOP_TEST_ASSETS"], illegal_local_path
    )
    try:
        context.item = context.dataset.items.upload(
            local_path=illegal_local_path, remote_path=None
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u"I download items to buffer")
def step_impl(context):
    items = context.dataset.items.get_all_items()
    context.buffer = context.dataset.items.download(
        items=items,
        save_locally=False,
        local_path=None,
        annotation_options=None,
    )


@behave.given(u"I delete all items from host")
def step_impl(context):
    context.item_list = context.dataset.items.list()
    for item in context.item_list.items:
        if item.type != "dir":
            context.dataset.items.delete(item_id=item.id)
    context.item_list = context.dataset.items.list()
    assert len(context.item_list.items) == 0


@behave.when(u"I upload items from buffer to host")
def step_impl(context):
    context.items_uploaded = 0
    for buff in context.buffer:
        uploaded_filename = "file" + str(context.items_uploaded) + ".jpg"
        buff.name = uploaded_filename
        context.items_uploaded += 1
        item = context.dataset.items.upload(buff, remote_path=None)
        # wait for platform attributes
        limit = 10 * 30
        stat = time.time()
        while True:
            time.sleep(3)
            item = context.dataset.items.get(item_id=item.id)
            if "video" in item.mimetype:
                if item.fps is not None:
                    break
            elif item.mimetype is not None:
                break
            if time.time() - stat > limit:
                raise TimeoutError("Timeout while waiting for platform attributes")


@behave.then(u"Number of error files should be larger by one")
def step_impl(context):
    assert context.error_logs_before + 1 == context.error_logs_after


@behave.then(u'There are "{item_count}" items in host')
def step_impl(context, item_count):
    filters = context.dl.Filters()
    filters.add(field='type', values='file')
    context.item_list = context.dataset.items.list(filters=filters)
    assert len(context.item_list.items) == int(item_count) == context.items_uploaded


@behave.when(u'I use a buffer to upload the file in path "{local_path}" with remote name "{remote_name}"')
def step_impl(context, local_path, remote_name):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)

    with open(local_path, "rb") as f:
        buffer = io.BytesIO(f.read())

    context.item = context.dataset.items.upload(local_path=buffer, remote_name=remote_name)


@behave.then(u'Item mimetype is the item type "{item_type}"')
def step_impl(context, item_type):
    assert context.item.metadata['system']['mimetype'].split('/')[1] == item_type


@behave.when(u'There are "{item_count}" items')
def step_impl(context, item_count):
    filepath = "0000000162.jpg"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)

    filename = 'file'
    counter = 0
    while counter < int(item_count):
        uploaded_filename = filename + str(counter) + '.jpg'
        import io
        with open(filepath, 'rb') as f:
            buffer = io.BytesIO(f.read())
            buffer.name = uploaded_filename
        context.dataset.items.upload(
            local_path=buffer,
            remote_path=None
        )
        counter += 1


@behave.when(u'There are "{item_count}" videos')
@behave.given(u'There are "{item_count}" videos')
def step_impl(context, item_count):
    filepath = "sample_video.mp4"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)
    filename = 'file'
    counter = 0
    while counter < int(item_count):
        uploaded_filename = filename + str(counter) + '.mp4'
        import io
        with open(filepath, 'rb') as f:
            buffer = io.BytesIO(f.read())
            buffer.name = uploaded_filename
        context.dataset.items.upload(
            local_path=buffer,
            remote_path=None
        )
        counter += 1
