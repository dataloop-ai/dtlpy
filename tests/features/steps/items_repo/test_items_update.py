import behave
import os
import time
import logging
import json
from .. import fixtures
import threading


@behave.when(u'I update items name to "{name}"')
def step_impl(context, name):
    context.item.filename = name
    context.item_update = context.dataset.items.update(item=context.item)

@behave.when('I update items name to "{name1}" and "{name2}" at the same time')
def step_impl(context, name1, name2):
    # context.item.filename = name1
    # context.item_update = context.dataset.items.update(item=context.item)
    def update_name(new_name):
        context.item.filename = new_name
        context.item_update = context.dataset.items.update(item=context.item)

    context.buffer1 = threading.Thread(target=update_name, args=(name1,))
    context.buffer2 = threading.Thread(target=update_name, args=(name2,))
    context.buffer1.start()
    context.buffer2.start()
    context.buffer1.join()
    context.buffer2.join()


@behave.then(u'I receive an Item object with name "{name}"')
def step_impl(context, name):
    assert type(context.item_update) == context.dl.Item
    assert context.item_update.filename == name

@behave.then(u'I receive an Item object with names "{name1}" or "{name2}"')
def step_impl(context, name1, name2):
    assert isinstance(context.item_update, context.dl.Item)
    assert context.item_update.filename in (name1, name2)


@behave.then(u"Only name attributes was changed")
def step_impl(context):
    item_get_json = context.item_get.to_json()
    original_item_json = context.item.to_json()
    item_get_json.pop("filename")
    original_item_json.pop("filename")
    item_get_json.pop("name")
    original_item_json.pop("name")
    item_get_json.pop("metadata")
    original_item_json.pop("metadata")
    item_get_json.pop("updatedAt")
    original_item_json.pop("updatedAt")
    item_get_json.pop("updatedBy")
    original_item_json.pop("updatedBy")

    assert item_get_json == original_item_json, "TEST FAILED: Expected : {}, Got: {}".format(original_item_json,
                                                                                             item_get_json)


@behave.then(u'Item in host was changed to "{name}"')
def step_impl(context, name):
    time.sleep(3)
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    if context.item_get.filename != name:
        logging.error(
            "item_get name = {item_get_name}, name should be {name_should}".format(
                item_get_name=context.item_get.filename, name_should=name
            )
        )
    assert context.item_get.filename == name

@behave.then(u'Item in host was changed to name "{name1}" or "{name2}"')
def step_impl(context, name1, name2):
    time.sleep(3)
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    if context.item_get.filename not in (name1, name2):
        logging.error(
            "item_get name = {item_get_name}, expected {name1} or {name2}".format(
                item_get_name=context.item_get.filename, name1=name1, name2=name2
            )
        )
    assert context.item_get.filename in (name1, name2)


@behave.given(u'And There is an item by the name of "{name}"')
def step_impl(context, name):
    local_path = "0000000162.jpg"
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)
    context.item = context.dataset.items.upload(
        local_path=local_path, remote_path=None
    )


@behave.then(u'PageEntity has directory item "{dir_name}"')
def step_impl(context, dir_name):
    filters = context.dl.Filters()
    filters.add(field="type", values="dir")
    page = context.dataset.items.list(filters=filters)
    dir_exist = False
    for item in page.items:
        if item.filename == dir_name:
            dir_exist = True
            break
    assert dir_exist is True


@behave.when(u'I update item system metadata with system_metadata="{param}"')
def step_impl(context, param):
    system_metadata = param == "True"
    context.original_item_json = context.item.to_json()
    context.item.metadata["system"]["modified"] = "True"
    context.item_update = context.dataset.items.update(item=context.item, system_metadata=system_metadata)


@behave.then(u"Then I receive an Item object")
def step_impl(context):
    assert type(context.item_update) == context.dl.Item


@behave.then(u"Item in host has modified metadata")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert "modified" in context.item_get.metadata["system"]


@behave.then(u"Only metadata was changed")
def step_impl(context):
    item_get_json = context.item_get.to_json()
    item_get_json.pop("metadata")
    context.original_item_json.pop("metadata")
    item_get_json.pop("updatedAt")
    context.original_item_json.pop("updatedAt")

    assert item_get_json == context.original_item_json


@behave.then(u"Item in host was not changed")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert "modified" not in context.item_get.metadata["system"]


@behave.given(u'I add folder "{folder_name}" to context.dataset')
def step_impl(context, folder_name):
    context.dataset.items.make_dir(directory="/{}".format(folder_name))


@behave.when(u'I Show annotation thumbnail for the item')
def step_impl(context):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], "api", "api_assets.json")
    with open(file_path, 'r') as file:
        json_obj = json.load(file)

    context.req = json_obj.get("annotation_thumbnail")
    fixtures.update_nested_structure(context, context.req.get('json_req', None))

    context.response = fixtures.gen_request(context=context, method="post", req=context.req, num_try=1, interval=0)

    response_json = context.response.json()
    command = context.dl.Command.from_json(_json=response_json,
                                           client_api=context.dl.client_api)
    command = command.wait(timeout=0)
    assert command, f"TEST FAILED: Command failed ID {command.id}"
    context.item = context.dataset.items.get(item_id=context.item.id)
    if not hasattr(context, 'thumbnail_id'):
        context.thumbnail_id = context.item.metadata['system'].get('annotationQueryThumbnailIdMap', {}).get('default')


@behave.when(u'I try to update item with params')
def step_impl(context):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']
    try:
        context.item_update = context.dataset.items.update(item=eval(params.get('item', "context.item")),
                                                           filters=eval(params.get('filters', "None")),
                                                           update_values=eval(params.get('update_values', "None")),
                                                           system_update_values=eval(
                                                               params.get('system_update_values', "None")),
                                                           system_metadata=eval(params.get('system_metadata', "False")),
                                                           )
        context.error = None
    except Exception as e:
        context.error = e
