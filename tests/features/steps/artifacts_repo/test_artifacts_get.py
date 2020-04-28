import behave
import dictdiffer


@behave.when(u'I get artifact by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'name':
        context.artifact_get = context.project.artifacts.get(artifact_name=context.artifact.name)
    elif get_method == 'id':
        context.artifact_get = context.project.artifacts.get(artifact_id=context.artifact.id)
    elif get_method == 'package_name':
        context.artifact_get = context.project.artifacts.get(package_name=context.package.name,
                                                             artifact_name=context.artifact.name)
    elif get_method == 'execution_id':
        context.artifact_get = context.project.artifacts.get(execution_id=context.execution.id,
                                                             artifact_name=context.artifact.name)
    elif get_method.startswith('wrong'):
        try:
            if get_method == 'wrong_artifact_name':
                context.artifact_get = context.project.artifacts.get(artifact_name=get_method)
            elif get_method == 'wrong_package_name':
                context.artifact_get = context.project.artifacts.get(package_name=get_method,
                                                                     artifact_name=context.artifact.name)
            elif get_method == 'wrong_artifact_id':
                context.artifact_get = context.project.artifacts.get(artifact_id=get_method)
            elif get_method == 'wrong_execution_id':
                context.artifact_get = context.project.artifacts.get(execution_id=get_method,
                                                                     artifact_name=context.artifact.name)
        except Exception as e:
            context.error = e


@behave.then(u'I receive an Artifact entity')
def step_impl(context):
    assert isinstance(context.artifact, context.dl.entities.Artifact)


@behave.then(u'Artifact received equals to the one uploaded')
def step_impl(context):
    original_json = context.artifact.to_json()
    get_json = context.artifact_get.to_json()
    original_json['metadata'].pop('system', None)
    get_json['metadata'].pop('system', None)
    original_json.pop('annotations', None)
    get_json.pop('annotations', None)
    if original_json == get_json:
        assert True
    else:
        diffs = list(dictdiffer.diff(original_json, get_json))
        print(diffs)
        assert False
