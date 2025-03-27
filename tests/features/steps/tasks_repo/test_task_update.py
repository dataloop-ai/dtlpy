import behave


@behave.when(u'I update task name "{task_name}"')
def step_impl(context, task_name):
    context.task.name = task_name
    context.task.update()


@behave.when(u'I update task owner "{task_owner}"')
def step_impl(context, task_owner):
    context.task.task_owner = task_owner
    context.task.update()


@behave.when(u'I update task due_date {due_date}')
def step_impl(context, due_date):
    context.task.due_date = due_date
    context.task.update()


@behave.when(u'I update task priority {priority}')
def step_impl(context, priority):
    context.task.priority = priority
    context.task.update()


@behave.then(u'I verify task "{filed}" = "{value}"')
def step_impl(context, filed, value):
    if filed == 'priority':
        assert context.task.priority == value, f"TEST FAILED: Filed = {filed}, Expected - {value}, Actual - {context.task.priority}"
    elif filed == 'task_owner':
        assert context.task.task_owner == value, f"TEST FAILED: Filed = {filed}, Expected - {value}, Actual - {context.task.task_owner}"
    elif filed == 'name':
        assert context.task.name == value, f"TEST FAILED: Filed = {filed}, Expected - {value}, Actual - {context.task.name}"
    elif filed == 'due_date':
        assert context.task.due_date == value, f"TEST FAILED: Filed = {filed}, Expected - {value}, Actual - {context.task.due_date}"
    else:
        print('Wrong filed - Expected filed = priority/ due_date/ task_owner/ task_name')




