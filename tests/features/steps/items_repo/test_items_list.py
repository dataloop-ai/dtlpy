import time

import behave
import os


@behave.when(u'I list items')
def step_impl(context):
    context.list = context.dataset.items.list(filters=None,
                                              page_offset=0,
                                              page_size=100)


@behave.then(u'I receive a PageEntity object')
def step_impl(context):
    assert type(context.list) == context.dl.entities.PagedEntities


@behave.then(u'PageEntity next page items has length of "{item_count}"')
def step_impl(context, item_count):
    context.list.next_page()
    count = 0
    for item in context.list.items:
        if item.type == 'file':
            count += 1
    assert count == int(item_count)


@behave.then(u'Item in PageEntity items equals item uploaded')
def step_impl(context):
    item_json = context.item.to_json()
    item_in_list_json = context.list.items[0].to_json()
    item_json.pop('metadata')
    item_in_list_json.pop('metadata')
    assert item_json == item_in_list_json


@behave.given(u'There are "{item_count}" items')
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


@behave.when(u'I list items with size of "{size}"')
def step_impl(context, size):
    context.list = context.dataset.items.list(filters=None,
                                              page_offset=0,
                                              page_size=int(size))


@behave.then(u'PageEntity items has next page')
def step_impl(context):
    assert context.list.has_next_page


@behave.then(u'PageEntity items does not have next page')
def step_impl(context):
    assert not context.list.has_next_page


@behave.then(u'PageEntity items has length of "{item_count}"')
def step_impl(context, item_count):
    assert len(context.list.items) == int(item_count)

    # if the is only one item we will same it to use later
    if int(item_count) == 1:
        for item in context.list.items:
            if item.type == 'file':
                context.item_in_page = item
                break


@behave.when(u'I list items with offset of "{offset}" and size of "{size}"')
def step_impl(context, offset, size):
    context.list = context.dataset.items.list(filters=None,
                                              page_offset=int(offset),
                                              page_size=int(size))


@behave.given(u'There is one item by the name of "{item_name}"')
def step_impl(context, item_name):
    filepath = "0000000162.jpg"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)
    import io
    with open(filepath, 'rb') as f:
        buffer = io.BytesIO(f.read())
        buffer.name = item_name
    context.item = context.dataset.items.upload(
        local_path=buffer,
        remote_path=None
    )


@behave.when(u'I list items with query filename="{filename_filter}"')
def step_impl(context, filename_filter):
    filters = context.dl.Filters()
    filters.add(field='filename', values=filename_filter)
    context.list = context.dataset.items.list(filters=filters)


@behave.then(u'PageEntity item received equal to item uploaded with name "test_name"')
def step_impl(context):
    item_in_page_json = context.item_in_page.to_json()
    item_json = context.item.to_json()
    item_in_page_json.pop('metadata')
    item_json.pop('metadata')
    assert item_in_page_json == item_json


@behave.given(u'There are "{item_count}" items in remote path "{remote_path}"')
def step_impl(context, item_count, remote_path):
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
            remote_path=remote_path
        )
        counter += 1


@behave.then(u'PageEntity items received have "{path}" in the filename')
def step_impl(context, path):
    for item in context.list.items:
        if item.type == 'file':
            assert path in item.filename


@behave.given(u'There are "{item_count}" .jpg items')
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


@behave.given(u'There is one .png item')
def step_impl(context):
    filepath = "0000000162.png"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)
    context.png_item = context.dataset.items.upload(
        local_path=filepath,
        remote_path=None
    )


@behave.when(u'I list items with query mimetypes="{mimetype_filters}"')
def step_impl(context, mimetype_filters):
    filters = context.dl.Filters()
    filters.add(field='type', values='file')
    filters.add(field='metadata.system.mimetype', values=mimetype_filters)
    context.list = context.dataset.items.list(filters=filters)


@behave.then(u'And PageEntity item received equal to .png item uploadede')
def step_impl(context):
    png_item_json = context.png_item.to_json()
    item_in_page_json = context.item_in_page.to_json()
    png_item_json.pop('metadata')
    item_in_page_json.pop('metadata')
    assert png_item_json == item_in_page_json


@behave.given(u'There is one .mp4 item')
def step_impl(context):
    filepath = "sample_video.mp4"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)
    context.item = context.item_mp4 = context.dataset.items.upload(
        local_path=filepath,
        remote_path=None
    )


@behave.when(u'I list items with query itemType="{value}"')
def step_impl(context, value):
    filters = context.dl.Filters()
    filters.add(field='type', values=value)
    context.list = context.dataset.items.list(filters=filters)


@behave.then(u'And PageEntity item received equal to .mp4 item uploadede')
def step_impl(context):
    mp4_item_json = context.item_mp4.to_json()
    item_in_page_json = context.item_in_page.to_json()
    mp4_item_json.pop('metadata')
    item_in_page_json.pop('metadata')
    assert mp4_item_json == item_in_page_json


@behave.when(u'I validate all items is annotated in dataset in index "{index}"')
@behave.when(u'I validate all items is annotated')
def step_impl(context, index=None):
    filters = context.dl.Filters()
    filters.add(field='annotated', values=False)
    num_try = 20
    interval = 15
    finished = False

    if index:
        dataset = context.datasets[int(index)]
    else:
        dataset = context.dataset

    for i in range(num_try):
        items_count = dataset.items.list(filters=filters).items_count
        if items_count == 0:
            finished = True
            break
        time.sleep(interval)

    assert finished, f"TEST FAILED: Not all items annotated , number left - {items_count}"
