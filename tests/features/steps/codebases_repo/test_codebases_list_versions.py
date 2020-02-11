import behave


@behave.when(u'I list versions of "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase_version_list = context.project.codebases.list_versions(codebase_name=codebase_name)


@behave.then(u'I receive a list of "{version_count}" versions')
def step_impl(context, version_count):
    assert len(context.codebase_version_list.items) == int(version_count)
