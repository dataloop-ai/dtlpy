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
    assert items[0]._src_item == context.item.id, f"TEST FAILED: filter by id _src_item id is {items[0]._src_item} while expected {context.item.id}"
