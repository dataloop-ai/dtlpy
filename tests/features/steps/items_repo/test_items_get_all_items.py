import behave


@behave.when(u'I get all items')
def step_impl(context):
    context.item_list = context.dataset.items.get_all_items()


@behave.then(u'I receive a list of "{item_count}" items')
def step_impl(context, item_count):
    assert len(context.item_list) == int(item_count), "Expected: {} , Got: {}\n".format(item_count, len(context.item_list))


@behave.when(u'I get all items, page size is "{page_size}"')
def step_impl(context, page_size):
    context.item_list = context.dataset.items.get_all_items(page_size=page_size)
