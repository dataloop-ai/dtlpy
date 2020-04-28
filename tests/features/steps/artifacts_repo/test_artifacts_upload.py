import behave
import os
from PIL import Image
import io


@behave.when(u'I upload "{upload_count}" artifacts to "{resource}"')
def step_impl(context, resource, upload_count):
    if resource == 'project':
        if int(upload_count) == 1:
            context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                                package_name=None,
                                                                package=None,
                                                                execution_id=None,
                                                                execution=None)
        else:
            image = Image.open(context.artifact_filepath)
            buffer = io.BytesIO()
            image.save(buffer, format='jpeg')
            for i in range(int(upload_count)):
                buffer.name = 'artifat_test_upload_{}'.format(i)
                context.artifact = context.project.artifacts.upload(filepath=buffer,
                                                                    package_name=None,
                                                                    package=None,
                                                                    execution_id=None,
                                                                    execution=None)
    elif resource == 'package':
        if int(upload_count) == 1:
            context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                                package_name=None,
                                                                package=context.package,
                                                                execution_id=None,
                                                                execution=None)
        else:
            image = Image.open(context.artifact_filepath)
            buffer = io.BytesIO()
            image.save(buffer, format='jpeg')
            for i in range(int(upload_count)):
                buffer.name = 'artifat_test_upload_{}'.format(i)
                context.artifact = context.project.artifacts.upload(filepath=buffer,
                                                                    package_name=None,
                                                                    package=context.package,
                                                                    execution_id=None,
                                                                    execution=None)
    elif resource == 'package_name':
        if int(upload_count) == 1:
            context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                                package_name=context.package.name,
                                                                package=None,
                                                                execution_id=None,
                                                                execution=None)
        else:
            image = Image.open(context.artifact_filepath)
            buffer = io.BytesIO()
            image.save(buffer, format='jpeg')
            for i in range(int(upload_count)):
                buffer.name = 'artifat_test_upload_{}'.format(i)
                context.artifact = context.project.artifacts.upload(filepath=buffer,
                                                                    package_name=context.package.name,
                                                                    package=None,
                                                                    execution_id=None,
                                                                    execution=None)
    elif resource == 'execution':
        if int(upload_count) == 1:
            context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                                package_name=None,
                                                                package=None,
                                                                execution_id=None,
                                                                execution=context.execution)
        else:
            image = Image.open(context.artifact_filepath)
            buffer = io.BytesIO()
            image.save(buffer, format='jpeg')
            for i in range(int(upload_count)):
                buffer.name = 'artifat_test_upload_{}'.format(i)
                context.artifact = context.project.artifacts.upload(filepath=buffer,
                                                                    package_name=None,
                                                                    package=None,
                                                                    execution_id=None,
                                                                    execution=context.execution)

    elif resource == 'execution_id':
        if int(upload_count) == 1:
            context.artifact = context.project.artifacts.upload(filepath=context.artifact_filepath,
                                                                package_name=None,
                                                                package=None,
                                                                execution_id=context.execution.id,
                                                                execution=None)
        else:
            image = Image.open(context.artifact_filepath)
            buffer = io.BytesIO()
            image.save(buffer, format='jpeg')
            for i in range(int(upload_count)):
                buffer.name = 'artifat_test_upload_{}'.format(i)
                context.artifact = context.project.artifacts.upload(filepath=buffer,
                                                                    package_name=None,
                                                                    package=None,
                                                                    execution_id=context.execution.id,
                                                                    execution=None)


@behave.given(u'Context "{attribute}" is "{str_value}"')
def step_impl(context, attribute, str_value):
    if 'filepath' in attribute:
        str_value = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], str_value)
    setattr(context, attribute, str_value)


@behave.then(u'I receive an artifact object')
def step_impl(context):
    assert isinstance(context.artifact, context.dl.entities.Artifact)
