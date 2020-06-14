import behave


@behave.when(u'I delete assignment by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'id':
        context.assignment_get = context.task.assignments.delete(assignment_id=context.assignment.id)
    elif get_method == 'name':
        context.assignment_get = context.task.assignments.delete(assignment_name=context.assignment.name)


@behave.when(u'I get an Assignment')
def step_impl(context):
    context.assignment = context.task.assignments.list()[0]


@behave.then(u'Assignment was deleted')
def step_impl(context):
    try:
        context.task.assignments.get(assignment_id=context.assignment.id)
        assert False
    except context.dl.exceptions.NotFound:
        assert True

