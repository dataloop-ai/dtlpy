import behave


@behave.when(u'I list Artifacts with "{param}"')
def step_impl(context, param):
    if param == 'package_name':
        context.artifacts_list = context.project.artifacts.list(package_name=context.package.name)
    elif param == 'execution_id':
        context.artifacts_list = context.project.artifacts.list(execution_id=context.execution.id)


@behave.then(u'I receive artifacts list of "{count}" items')
def step_impl(context, count):
    assert len(context.artifacts_list) == int(count)
