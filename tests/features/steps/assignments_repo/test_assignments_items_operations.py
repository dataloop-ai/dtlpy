import os
import io
import behave


@behave.when(u'I get assignment items')
def step_impl(context):
    context.assignment_items = context.assignment.get_items()


@behave.then(u'I receive a list of "{count}" assignment items')
def step_impl(context, count):
    assert context.assignment_items.items_count == int(count)


@behave.when(u'I add "{count}" items to assignment')
def step_impl(context, count):
    local_path = '0000000162.jpg'
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)
    with open(local_path, "rb") as f:
        buffer = io.BytesIO(f.read())
    items = list()
    for i in range(int(count)):
        buffer.name = 'item-{}'.format(i)
        items.append(context.dataset.items.upload(local_path=buffer))
    context.assignment.assign_items(items=items)


@behave.when(u'I delete all items from assignment')
def step_impl(context):
    context.assignment.remove_items(filters=context.dl.Filters())

