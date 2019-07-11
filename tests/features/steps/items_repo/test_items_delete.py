import behave
import os


@behave.given(u'There are no items')
def step_impl(context):
    filters = context.dl.Filters()
    filters.add(field='type', values='file')
    assert len(context.dataset.items.list(filters=filters).items) == 0


@behave.given(u'I upload an item by the name of "{item_name}"')
def step_impl(context, item_name):
    local_path = '0000000162.jpg'
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    import io
    with open(local_path, 'rb') as f:
        buffer = io.BytesIO(f.read())
        buffer.name = item_name

    context.item = context.dataset.items.upload(local_path=buffer)
    context.item = context.dataset.items.get(filepath=item_name)
    context.item_count = 1


@behave.when(u'I delete the item by name')
def step_impl(context):
    context.dataset.items.delete(filename=context.item.filename)


@behave.then(u'There are no items')
def step_impl(context):
    filters = context.dl.Filters()
    filters.add(field='type', values='file')
    assert len(context.dataset.items.list(filters=filters).items) == 0


@behave.when(u'I delete the item by id')
def step_impl(context):
    context.dataset.items.delete(item_id=context.item.id)


@behave.when(u'I try to delete an item by the name of "{item_name}"')
def step_impl(context, item_name):
    try:
        context.dataset.items.delete(filename=item_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No item was deleted')
def step_impl(context):
    filters = context.dl.Filters()
    filters.add(field='type', values='file')
    assert len(context.dataset.items.list(filters=filters).items) == context.item_count


@behave.when(u'I try to delete an item by the id of "{item_id}"')
def step_impl(context, item_id):
    try:
        context.dataset.items.delete(item_id=item_id)
        context.error = None
    except Exception as e:
        context.error = e
