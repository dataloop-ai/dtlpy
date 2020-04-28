import behave
import os


@behave.when(u'I download artifact by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'name':
        context.artifact_get = context.project.artifacts.download(artifact_name=context.artifact.name)
    elif get_method == 'id':
        context.artifact_get = context.project.artifacts.download(artifact_id=context.artifact.id)
    elif get_method == 'package_name':
        context.artifact_get = context.project.artifacts.download(package_name=context.package.name)
    elif get_method == 'execution_id':
        context.artifact_get = context.project.artifacts.download(execution_id=context.execution.id)


@behave.then(u'Artifact "{resource}" was downloaded successfully')
def step_impl(context, resource):
    if not isinstance(context.artifact_get, list):
        context.artifact_get = [context.artifact_get]

    assert len(context.artifact_get) > 0

    for artifact_get in context.artifact_get:
        assert os.path.isfile(artifact_get)
        if resource == 'folder':
            assert os.path.basename(context.artifact_filepath) in artifact_get
    if hasattr(context, 'by_execution_id') and context.by_execution_id:
        assert len(context.artifact_get) == 1


@behave.given(u'Context has attribute execution_id = True')
def step_impl(context):
    context.by_execution_id = True
