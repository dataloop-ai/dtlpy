import behave
import os

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
