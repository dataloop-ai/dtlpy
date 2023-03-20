import behave


@behave.when(u'I update assignment name "{assignment_name}"')
def step_impl(context, assignment_name):
    context.assignment.name = assignment_name
    context.assignment.update()