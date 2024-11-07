import behave
import os
import time


@behave.given(u"There is an item")
def step_impl(context):
    filepath = "0000000162.jpg"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)
    context.item = context.dataset.items.upload(local_path=filepath)


@behave.when(u"I get the item by id")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)


@behave.then(u"I receive an Item object")
def step_impl(context):
    assert type(context.item_get) == context.dl.Item


@behave.then(u"The item I received equals the item I uploaded")
def step_impl(context):
    item_json = context.item.to_json()
    item_get_json = context.item_get.to_json()
    item_json.pop('metadata')
    item_get_json.pop('metadata')
    assert item_json == item_get_json


@behave.when(u'I try to get item by "{some_id}"')
def step_impl(context, some_id):
    try:
        context.dataset.items.get(some_id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I get the item by remote path "{remote_path}"')
def step_impl(context, remote_path):
    context.item_get = context.dataset.items.get(filepath=remote_path)


@behave.when(u'I try to get an item by remote path "{remote_path}"')
def step_impl(context, remote_path):
    try:
        context.dataset.items.get(filepath=remote_path)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to use get services with no params')
def step_impl(context):
    try:
        context.dataset.items.get()
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u'There are 2 items by the name of "{file_name}"')
def step_impl(context, file_name):
    filepath = "0000000162.jpg"
    filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], filepath)

    context.dataset.items.upload(
        local_path=filepath,
        remote_path=None
    )

    remote_path = '/folder_name/'
    context.dataset.items.upload(
        local_path=filepath,
        remote_path=remote_path
    )


@behave.then(u'I get items by dataset Id')
def step_impl(context):
    success, response = context.dl.client_api.gen_request(
        req_type="get",
        path="/datasets/{}/items".format(context.dataset.id)
    )
    assert success, "TEST FAILED: Error message: {}".format(response.json())


@behave.when(u'I get a consensus item')
def step_impl(context):
    context.folder_name = None
    for dir_name in context.dataset.directory_tree.dir_names:
        if "/.consensus/" in dir_name:
            context.folder_name = dir_name

    assert context.folder_name, f"TEST FAILED: Folder doesn't exists in: {context.dataset.directory_tree.dir_names}"

    filters = context.dl.Filters()
    filters.add(field='dir', values=[context.folder_name], operator='in')
    filters.add(field='hidden', values=True)

    assert context.dataset.items.list(filters=filters).items_count, "TEST FAILED: No consensus items in dataset"

    context.item = context.dataset.items.list(filters=filters).items[0]


@behave.when(u'Dataset in index "{index}" have "{items_count}" items')
def step_impl(context, index, items_count):
    dataset = context.datasets[int(index)]
    num_try = 16
    interval = 10
    finished = False

    for i in range(num_try):
        if dataset.items.list().items_count == int(items_count):
            finished = True
            break
        time.sleep(interval)

    assert finished, f"TEST FAILED: Expected: {items_count} items , Actual: {dataset.items.list().items_count}"


@behave.when(u"I get item thumbnail id")
def step_impl(context):
    context.item = context.dataset.items.get(item_id=context.item.id)
    context.item_thumbnail_id = context.item.metadata['system']['thumbnailId']


@behave.then(u'I validate item thumbnail id is "{condition}" to the previous thumbnail id')
def step_impl(context, condition):
    if not hasattr(context, 'item_thumbnail_id'):
        assert False, "TEST FAILED: Please make sure to run the step - 'When I get item thumbnail id'"
    context.item = context.dataset.items.get(item_id=context.item.id)
    error_message = f"TEST FAILED: Item thumbnail is not {condition}"
    if condition == "not-equal":
        assert context.item.metadata['system']['thumbnailId'] != context.item_thumbnail_id, error_message
    elif condition == "equal":
        assert context.item.metadata['system']['thumbnailId'] == context.item_thumbnail_id, error_message
    else:
        raise ValueError("condition must be 'different' or 'equal'")


@behave.then(u'I should see a thumbnail v2 on the item')
def step_impl(context):
    """
    Make sure to run the step - 'I Show annotation thumbnail for the item' before running this step
    """
    assert context.item.metadata['system'].get('annotationQueryThumbnailIdMap', {}).get(
        'default') is not None, f"TEST FAILED: No thumbnail v2 on the item {context.item.metadata['system']}"
    thumbnail_id = context.item.metadata['system']['annotationQueryThumbnailIdMap']['default']
    try:
        context.dataset.items.get(item_id=thumbnail_id)
    except context.dl.exceptions.NotFound:
        assert False, f"TEST FAILED: Thumbnail v2 not found in dataset items with Id {thumbnail_id}"


@behave.then(u'I should not see a thumbnail v2 on the item')
def step_impl(context):
    """
    Make sure to run the step - 'I Show annotation thumbnail for the item' before running this step
    """
    assert context.item.metadata['system'].get('annotationQueryThumbnailIdMap', {}).get(
        'default') is None, f"TEST FAILED: Thumbnail v2 on the item {context.item.metadata['system']}"
    try:
        context.dataset.items.get(item_id=context.thumbnail_id)
    except context.dl.exceptions.NotFound:
        pass


@behave.then(u'I validate "{value}" not in item system metadata')
def step_impl(context, value):
    item = context.dataset.items.get(item_id=context.item.id)
    value = eval(value)
    # Check if the value key exists in item metadata system key
    if value.keys() <= item.metadata['system'].keys():
        for key in value.keys():
            assert value[key] != item.metadata['system'][
                key], f"TEST FAILED: {value} found in item system metadata, {item.metadata['system']}"

