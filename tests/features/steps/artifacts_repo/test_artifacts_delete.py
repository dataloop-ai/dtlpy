import behave


@behave.when(u'I delete artifact by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'name':
        context.artifact_get = context.project.artifacts.delete(artifact_name=context.artifact.name)
    elif get_method == 'id':
        context.artifact_get = context.project.artifacts.delete(artifact_id=context.artifact.id)
    elif get_method == 'package_name':
        context.artifact_get = context.project.artifacts.delete(package_name=context.package.name)
    elif get_method == 'execution_id':
        context.artifact_get = context.project.artifacts.delete(execution_id=context.execution.id)


@behave.then(u'Artifact does not exist "{resource}"')
def step_impl(context, resource):
    artifacts = None
    if resource == 'name':
        try:
            artifacts = context.project.artifacts.get(artifact_name=context.artifact.name)
        except Exception:
            artifacts = list()
    elif resource == 'id':
        try:
            artifacts = context.project.artifacts.get(artifact_id=context.artifact.id)
        except Exception:
            artifacts = list()
    elif resource == 'package_name':
        artifacts = context.project.artifacts.list(package_name=context.package.name)
    elif resource == 'execution_id':
        artifacts = context.project.artifacts.list(execution_id=context.execution.id)

    assert artifacts is not None

    if not isinstance(artifacts, list):
        artifacts = [artifacts]

    assert len(artifacts) == 0
