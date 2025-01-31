import behave


@behave.then(u'I validate _src_item is not None')
def step_impl(context):
    item = context.dataset.items.get(item_id=context.item.id)
    assert item._src_item, "TEST FAILED: Failed get _src_item by item.get"
    filters = context.dl.Filters(use_defaults=False, field='id', values=context.item.id)
    items = list(context.item.dataset.items.list(filters=filters).all())
    assert items[0]._src_item, "TEST FAILED: Failed get _src_item by dataset.items.list(filters=filters)"


@behave.then(u'I validate cloned item has the correct src item')
def step_impl(context):
    item = context.dataset.items.get(item_id=context.cloned_item.id)
    assert item._src_item == context.item.id, f"TEST FAILED: get by id _src_item id is {item._src_item} while expected {context.item.id}"
    filters = context.dl.Filters(use_defaults=False, field='id', values=context.cloned_item.id)
    items = list(context.item.dataset.items.list(filters=filters).all())
    assert items[
               0]._src_item == context.item.id, f"TEST FAILED: filter by id _src_item id is {items[0]._src_item} while expected {context.item.id}"


@behave.then(u'I validate item is annotated')
def step_impl(context):
    item = context.dataset.items.get(item_id=context.item.id)
    assert item.annotated, "TEST FAILED: Expected item to be annotated"


@behave.when(u'I import item "{name}" from "{path}"')
def step_impl(context, path, name):
    if path == 'root':
        success, response = context.dl.client_api.gen_request(
            req_type="post",
            path=f"/datasets/{context.dataset.id}/imports",
            json_req=[{"filename": name, "storageId": name}],
        )
    else:
        success, response = context.dl.client_api.gen_request(
            req_type="post",
            path=f"/datasets/{context.dataset.id}/imports",
            json_req=[{"filename": name, "storageId": f"{path}/{name}"}],
        )

    if not success:
        raise context.dl.exceptions.PlatformException(response)
    item = context.dataset.items.get(filepath="/" + name)
    if item.creator is None:
        assert False, f"FAILED - item creator = {item.creator}"
