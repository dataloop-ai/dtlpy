import types

import behave


@behave.when(u'I Add description "{text}" to item')
def step_impl(context, text):
    context.item = context.item.set_description(text)


@behave.then(u'I validate item.description has "{text}" value')
def step_impl(context, text):
    context.item = context.dl.items.get(item_id=context.item.id)
    assert context.item.description == text


@behave.then(u'i remove description from the root')
def step_impl(context):
    item_json = context.item.to_json()
    item_json['metadata']['user'] = {'remove': 'description'}
    item_json.pop('description')

    def new_to_json(self):
        return item_json

    funcType = types.MethodType
    context.origin_to_json = context.item.to_json
    context.origin_from_json = context.dl.Item.from_json
    context.item.to_json = funcType(new_to_json, context.item)
    context.item = context.item.update(True)
    assert context.item.metadata['user'] == {'remove': 'description'}


@behave.then(u'Return from and to Json functions to the original implementation')
def step_impl(context):
    funcType = types.MethodType
    context.item.to_json = funcType(context.origin_to_json, context.item)
    context.dl.Item.from_json = context.origin_from_json


@behave.when(u'i add new field to the root')
def step_impl(context):
    context.origin_to_json = context.item.to_json
    context.origin_from_json = context.dl.Item.from_json
    item_json = context.item.to_json()
    item_json['newField'] = 'newField'

    def new_to_json(self):
        return item_json

    def new_from_json(client_api, _json, dataset):
        return _json

    funcType = types.MethodType
    context.item.to_json = funcType(new_to_json, context.item)
    context.dl.Item.from_json = new_from_json
    context.item_new_from_json = context.item.update(True)
    print()


@behave.when(u'new field do not added')
def step_impl(context):
    assert 'newField' not in context.item_new_from_json


@behave.then(u'I remove item.description')
def step_impl(context):
    context.item.description = None


@behave.then(u'I validate item.description is None')
def step_impl(context):
    context.item = context.dl.items.get(item_id=context.item.id)
    assert context.item.description == None


@behave.then(u'I update the metadata')
def step_impl(context):
    context.original_item_json = context.item.to_json()
    context.item.metadata["system"]["modified"] = "Update"
    context.item_update = context.dataset.items.update(item=context.item, system_metadata=True)


@behave.then(u"Item was modified metadata")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert "modified" in context.item_get.metadata["system"]
    assert "Update" == context.item_get.metadata["system"]["modified"]


@behave.then(u'I remove the added metadata')
def step_impl(context):
    context.original_item_json = context.item.to_json()
    context.item.metadata["system"]["modified"] = None
    context.item_update = context.dataset.items.update(item=context.item, system_metadata=True)


@behave.then(u"metadata was deleted")
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert "modified" not in context.item_get.metadata["system"]
