import behave


@behave.when(u'I delete task by "{delete_method}"')
def step_impl(context, delete_method):
    if delete_method == 'name':
        context.task_get = context.project.tasks.delete(task_name=context.task.name)
    elif delete_method == 'id':
        context.task_get = context.project.tasks.delete(task_id=context.task.id)
    elif delete_method == 'object':
        context.task_get = context.project.tasks.delete(task=context.task)
    else:
        assert False, "Failed, Wrong delete_method (name / id / object)"


@behave.when(u'I delete qa_task by "{delete_method}"')
def step_impl(context, delete_method):
    if delete_method == 'name':
        context.task_get = context.project.tasks.delete(task_name=context.qa_task.name)
    elif delete_method == 'id':
        context.task_get = context.project.tasks.delete(task_id=context.qa_task.id)
    elif delete_method == 'object':
        context.task_get = context.project.tasks.delete(task=context.qa_task)
    else:
        assert False, "Failed, Wrong delete_method (name / id / object)"


@behave.then(u'Task has been deleted')
def step_impl(context):
    try:
        context.project.tasks.get(taks_id=context.task.id)
        assert False
    except Exception:
        assert True
