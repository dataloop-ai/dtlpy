import behave
import os


@behave.when(u'I upload artifact to "{resource}"')
def step_impl(context, resource):
    if resource == 'project':
        context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                            package_name=None,
                                                            package=None,
                                                            execution_id=None,
                                                            execution=None)
    elif resource == 'package':
        context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                            package_name=None,
                                                            package=context.package,
                                                            execution_id=None,
                                                            execution=None)
    elif resource == 'package_name':
        context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                            package_name=context.package.name,
                                                            package=None,
                                                            execution_id=None,
                                                            execution=None)
    elif resource == 'execution':
        context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                            package_name=None,
                                                            package=None,
                                                            execution_id=None,
                                                            execution=context.execution)
    elif resource == 'execution_id':
        context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                            package_name=None,
                                                            package=None,
                                                            execution_id=context.execution.id,
                                                            execution=None)


@behave.given(u'Context "{attribute}" is "{str_value}"')
def step_impl(context, attribute, str_value):
    if 'filepath' in attribute:
        str_value = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], str_value)
    setattr(context, attribute, str_value)


@behave.then(u'I recieve an artifact object')
def step_impl(context):
    assert isinstance(context.artifact, context.dl.entities.Artifact)
