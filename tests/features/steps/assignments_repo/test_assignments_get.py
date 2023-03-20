import behave


@behave.when(u'I get Assignment by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'id':
        context.assignment_get = context.task.assignments.get(assignment_id=context.assignment.id)
    elif get_method == 'name':
        context.assignment_get = context.task.assignments.get(assignment_name=context.assignment.name)


@behave.then(u'I get an assignment entity')
def step_impl(context):
    assert isinstance(context.assignment_get, context.dl.entities.Assignment)


@behave.then(u'Assignment received equals assignment created')
def step_impl(context):
    assert context.assignment_get.to_json() == context.assignment.to_json()


@behave.given(u'I save dataset items to context')
def step_impl(context):
    context.items_in_dataset = context.dataset.items.list().items


@behave.when(u'I get assignment from task')
def step_impl(context):
    assert hasattr(context, "task"), "TEST FAILED: Please create a task with assignments before this step"
    context.assignment = context.task.assignments.list()[0]
