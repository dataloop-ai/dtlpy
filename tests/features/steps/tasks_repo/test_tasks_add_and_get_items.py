import behave
from .. import fixtures


@behave.when(u'I get Task items by "{method}"')
def step_impl(context, method):
    if method == 'name':
        context.task_items = context.dataset.tasks.get_items(task_name=context.task.name)
    elif method == 'id':
        context.task_items = context.dataset.tasks.get_items(task_id=context.task.id)


@behave.then(u'I receive task items list of "{count}" items')
def step_impl(context, count):
    success = context.task_items.items_count == int(count)
    for page in context.task_items:
        for item in page:
            success = success and isinstance(item, context.dl.Item)

    if not success:
        print('items received: {}'.format(context.task_items.items_count))

    assert success


@behave.when(u'I add items to task')
def step_impl(context):
    context.params = {param.split('=')[0]: fixtures.get_value(params=param.split('='), context=context) for param in
                      context.table.headings if
                      fixtures.get_value(params=param.split('='), context=context) is not None}
    context.dataset.tasks.add_items(**context.params)
