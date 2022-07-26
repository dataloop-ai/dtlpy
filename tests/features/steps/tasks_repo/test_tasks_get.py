import behave


@behave.when(u'I get Task by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'name':
        context.task_get = context.project.tasks.get(task_name=context.task.name)
    elif get_method == 'id':
        context.task_get = context.project.tasks.get(task_id=context.task.id)


@behave.when(u'I get Task by wrong "{get_method}"')
def step_impl(context, get_method):
    try:
        if get_method == 'name':
            context.task_get = context.project.tasks.get(task_name='randomName')
        elif get_method == 'id':
            context.task_get = context.project.tasks.get(task_id='111111111111')
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Task received equals task created')
def step_impl(context):
    assert context.task.to_json() == context.task_get.to_json()


