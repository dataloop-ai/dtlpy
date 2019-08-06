import behave
import os


@behave.given(u'Feature: There is a plugin')
def step_impl(context):
    context.project.plugins.generate_local_plugin(name='plugin')
    context.plugin = context.project.plugins.create(name='plugin')
    context.feature.plugin = context.plugin


@behave.when(u'I checkout')
def step_impl(context):
    entity = context.table.headings[0]
    if entity == 'project':
        context.dl.projects.checkout(identifier=context.project.name)
    elif entity == 'dataset':
        context.project.datasets.checkout(identifier=context.dataset.name)
    elif entity == 'plugin':
        context.project.plugins.checkout(plugin_name='plugin')
    else:
        assert False, 'Unknown entity param'


@behave.then(u'I am checked out')
def step_impl(context):
    entity = context.table.headings[0]
    if entity == 'project':
        assert context.dl.projects.get().id == context.project.id
    elif entity == 'dataset':
        assert context.project.datasets.get().id == context.dataset.id
    elif entity == 'plugin':
        assert context.project.plugins.get().id == context.plugin.id
    else:
        assert False, 'Unknown entity param'


@behave.given(u'Feature: I pack to project directory in "{plugin_package}"')
def step_impl(context, plugin_package):
    plugin_package = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], plugin_package)
    context.package = context.project.packages.pack(
        directory=plugin_package,
        name='plugin_package',
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
    if hasattr(context.feature, 'done_setting') and context.feature.done_setting:
        for param in context.table.headings:
            if param == 'dataset':
                context.dataset = context.feature.dataset
            elif param == 'plugin':
                context.plugin = context.feature.plugin

@behave.given(u'Done setting')
def step_impl(context):
    context.feature.done_setting = True
