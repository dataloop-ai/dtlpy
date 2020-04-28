import behave


@behave.when(u'I list assignments')
def step_impl(context):
    context.assignments_list = context.task.assignments.list()


@behave.then(u'I receive a list of "{count}" assignments')
def step_impl(context, count):
    assert len(context.assignments_list) == int(count)
    for ass in context.assignments_list:
        assert isinstance(ass, context.dl.entities.Assignment)
