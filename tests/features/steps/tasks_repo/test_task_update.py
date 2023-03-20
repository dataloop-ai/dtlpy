import behave
import dtlpy as dl


@behave.when(u'I update task name "{task_name}"')
def step_impl(context, task_name):
    context.task.name = task_name
    context.task.update()

