import behave
import os


@behave.when(u"I download batched items to buffer")
def step_impl(context):
    items = context.dataset.items.get_all_items()
    context.buffer = context.dataset.items.download(
        items=items,
        save_locally=False,
        local_path=None,
        annotation_options=None,
    )


@behave.when(u'I download batched items to local path "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    items = context.dataset.items.get_all_items()
    context.dataset.items.download(
        items=items,
        save_locally=True,
        local_path=local_path,
        annotation_options=None,
    )


@behave.then(u"I can upload items from buffer to host")
def step_impl(context):
    counter = 0
    for buff in context.buffer:
        uploaded_filename = "file" + str(counter) + '.jpg'
        buff.name = uploaded_filename
        counter += 1
        context.dataset.items.upload(
            buff,
            remote_path=None,
        )

    context.item_list = context.dataset.items.list()
    assert len(context.item_list.items) == counter


@behave.when(u'I delete all items from host')
def step_impl(context):
    context.item_list = context.dataset.items.list()
    for item in context.item_list.items:
        if item.type != 'dir':
            context.dataset.items.delete(item_id=item.id)
    context.item_list = context.dataset.items.list()
    assert len(context.item_list.items) == 0


@behave.when(u'I download items to local path "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    items = context.dataset.items.get_all_items()
    context.buffer = context.dataset.items.download(
        items=items,
        save_locally=True,
        local_path=local_path,
        annotation_options=None,
        overwrite=True
    )


@behave.then(u'Items are saved in "{local_path}"')
def step_impl(context, local_path):
    import cv2
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    compare_folder_path = 'downloaded_batch/should_be'
    compare_folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], compare_folder_path)

    for item in os.listdir(compare_folder_path):
        file_to_compare = os.path.join(compare_folder_path, item)
        original = cv2.imread(os.path.join(local_path, item))
        downloaded = cv2.imread(file_to_compare)
        if original.shape == downloaded.shape:
            difference = cv2.subtract(original, downloaded)
            b, g, r = cv2.split(difference)
            if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
                assert True
            else:
                assert False
        else:
            assert False
