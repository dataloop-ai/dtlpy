import behave


@behave.when(u'I get last model in project')
def step_impl(context):
    context.model = context.project.models.list().items[-1]
