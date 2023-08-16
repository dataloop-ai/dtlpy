import behave


@behave.when(u'I get the first assignment')
def step_impl(context):
    context.assignment = context.task.assignments.list()[0]


@behave.when(u'I redistribute assignment to "{new_assignees}"')
def step_impl(context, new_assignees):
    assignee_ids = new_assignees.split(',')
    workload = context.dl.Workload.generate(assignee_ids=assignee_ids)
    context.before_redistribution_item_ids = [item.id for item in context.assignment.get_items().items]
    context.redistributed = [ass for ass in context.assignment.redistribute(workload=workload) if ass.annotator in [ass_id.lower() for ass_id in assignee_ids]]


def compare_items_list(items_a, items_b):
    equals = len(items_b) == len(items_a)
    for item in items_a:
        equals = equals and item in items_b
    return equals


@behave.then(u'Assignments was redistributed to "{new_assignees}"')
def step_impl(context, new_assignees):
    assignee_ids = new_assignees.split(',')
    assert len(context.redistributed) == len(assignee_ids)
    items = list()
    for ass in context.redistributed:
        assert isinstance(ass, context.dl.entities.Assignment)
        items += ass.get_items().items
        assert ass.annotator in assignee_ids
    dest_item_ids = [item.id for item in items]

    assert compare_items_list(context.before_redistribution_item_ids, dest_item_ids)
