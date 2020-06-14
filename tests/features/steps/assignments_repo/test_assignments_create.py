import behave
from .. import fixtures


@behave.when(u'I create an Assignment from "{entity}" entity')
def step_impl(context, entity):
    context.params = {param.split('=')[0]: fixtures.get_assignment_value(params=param.split('='), context=context) for
                      param in context.table.headings if
                      fixtures.get_assignment_value(params=param.split('='), context=context) is not None}

    if entity != 'task':
        context.params['task'] = context.task

    if entity == 'task':
        context.assignment = context.task.assignments.create(**context.params)
    elif entity == 'dataset':
        context.assignment = context.dataset.assignments.create(**context.params)
    elif entity == 'project':
        context.assignment = context.project.assignments.create(**context.params)


@behave.then(u'I receive an assignment entity')
def step_impl(context):
    assert isinstance(context.task, context.dl.entities.Task)


def compare_items_list(items_a, items_b):
    equals = len(items_b) == len(items_a)
    for item in items_a:
        equals = equals and item in items_b
    return equals


@behave.then(u'Assignment has the correct attributes')
def step_impl(context):
    for key, val in context.params.items():
        if key == 'filters':
            assignment_items = [item.id for item in context.assignment.get_items().items]
            assert compare_items_list(items_a=assignment_items, items_b=context.dataset.items.list(filters=val).items)
        elif key == 'items':
            assignment_items = [item.id for item in context.assignment.get_items().items]
            assert compare_items_list(items_a=assignment_items, items_b=[item.id for item in val])
        elif key == 'assignee_ids':
            assert context.assignment.annotator == val
        elif key == 'dataset':
            assert context.assignment.dataset_id == val.id
        elif key == 'project_id':
            assert context.assignment.project_id == val
        elif key == 'status':
            assert context.assignment.status == val
        elif key == 'metadata':
            assert context.assignment.metadata[list(val.keys())[0]] == val[list(val.keys())[0]]
