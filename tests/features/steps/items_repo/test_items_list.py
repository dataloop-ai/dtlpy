import time
import dtlpy as dl
import behave
import os


@behave.when(u'I list items')
def step_impl(context):
    context.list = context.dataset.items.list(filters=None,
                                              page_offset=0,
                                              page_size=100)


@behave.when(u'I get item from task')
def step_impl(context):
    context.item = context.task.get_items().items[0]


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
        context.item = context.dataset.items.upload(
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
    num_try = 48
    interval = 5
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


@behave.when(u'I list items with page_size "{n:d}"')
def step_list_with_page_size(context, n):
    context.first_page = context.dataset.items.list(
        filters=None,
        page_offset=0,
        page_size=n
    )
    context.first_items = list(context.first_page.items)
    assert context.first_items, "First page has no items!"
    context.last_seen_id = context.first_page.last_seen_id
    assert context.last_seen_id is not None, "Expected last_seen_id to be set on first_page"


@behave.then(u'I record the last_seen_id from that page')
def step_record_items_cursor(context):
    assert hasattr(context, 'first_page'), "first_page was not set"
    cursor = getattr(context.first_page, 'last_seen_id', None)
    assert cursor is not None, "Expected first_page.last_seen_id to be populated"
    context.last_seen_id = cursor


@behave.when(u'I list items after last_seen_id with page_size "{n:d}"')
def step_list_items_after_cursor(context, n):
    f = dl.Filters()
    f.page = 0 
    f.page_size = n
    f.add(
        field="id",
        values=context.last_seen_id,
        operator=dl.FiltersOperations.GREATER_THAN,
        method=dl.FiltersOperations.AND
    )

    context.second_page = context.dataset.items.list(filters=f)
    context.second_items = list(context.second_page.items)
    assert context.second_items, "Second page has no items!"


@behave.then(u'I should receive "{count:d}" item')
def step_assert_item_count(context, count):
    items = getattr(context, 'second_items', None) or context.first_items
    actual = len([i for i in items if i.type == 'file'])
    assert actual == count, f"Expected {count}, got {actual}"


@behave.then(u'that item’s id should differ from the first page’s id')
def step_assert_item_distinct(context):
    first_id  = context.first_items[0].id
    second_id = context.second_items[0].id
    print(f"▶ First page last_seen_id: {context.last_seen_id}")
    print(f"▶ First item ID: {context.first_items[0].id}")  
    print(f"▶ Second item ID: {context.second_items[0].id}")
    assert second_id != first_id, \
        f"Expected second-page id to differ; got both = {first_id}"
