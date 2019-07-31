import behave
import dtlpy
import os


@behave.given(u'Feature: There is a plugin')
def step_impl(context):
    assert isinstance(context.project, dtlpy.entities.Project)
    context.plugin = context.project.plugins.create(name='plugin',
                                                    package=context.package
                                                    )


@behave.when(u'I checkout')
def step_impl(context):
    entity = context.table.headings[0]
    if entity == 'project':
        context.dl.projects.checkout(identifier=context.project.name)
    elif entity == 'project':
        context.project.datasets.checkout(identifier=context.dataset.name)
    elif entity == 'project':
        context.project.plugins.checkout(identifier=context.plugin.name)
    else:
        assert False, 'Unknown entity param'


@behave.then(u'I am checked out')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then I an checked out')


@behave.given(u'Feature: I pack to project directory in "{plugin_package}"')
def step_impl(context, plugin_package):
    context.package = context.project.packages.pack(
        directory=context.package_local_dir,
        name=plugin_package,
        description="some description",
    )


@behave.given(u'Feature: There is a Package directory with a python file in path "{code_path}"')
def step_impl(context, code_path):
    code_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], code_path)
    dirs = os.listdir(code_path)
    assert "some_code.py" in dirs
    context.feature.package_local_dir = code_path


@behave.given(u'Feature: I create a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.feature.dataset = context.project.datasets.create(dataset_name=dataset_name)


@behave.given(u'Get feature entities')
def step_impl(context):
    for param in context.table.headings:
        if param == 'dataset':
            context.dataset = context.feature.dataset
        elif param == 'package':
            context.dataset = context.feature.dataset
        elif param == 'plugin':
            context.dataset = context.feature.dataset
