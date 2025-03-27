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
@behave.when(u'I get assignment from task with assignee "{assignee}"')
def step_impl(context, assignee=None):
    # Ensure 'task' exists in context
    assert hasattr(context, "task"), "TEST FAILED: Please create a task with assignments before this step"
    # Get the list of assignments from the task
    assignments = context.task.assignments.list()
    # Iterate through the list of assignments
    for assignment in assignments:
        # Check if the remaining status is not 0
        if assignment.item_status["remaining"] != 0 and (assignee is None or assignee == assignment.annotator):
            # Assign it to context.assignment
            context.assignment = assignment
            break
    else:
        # If no assignment with remaining != 0 is found
        raise AssertionError("TEST FAILED: No assignments with remaining items.")
