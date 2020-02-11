import behave
import os


@behave.given(u'Feature: There is a package')
def step_impl(context):
    src_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], 'packages_checkout_create')
    context.package = context.project.packages.push(src_path=src_path)
    context.feature.package = context.package


@behave.given(u'Feature: There is a service')
def step_impl(context):
    src_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], 'packages_checkout_create')
    context.service = context.package.services.deploy_from_local_folder(cwd=src_path)
    context.feature.service = context.service


@behave.when(u'I checkout')
def step_impl(context):
    entity = context.table.headings[0]
    if entity == 'project':
        context.project.checkout()
    elif entity == 'dataset':
        context.dataset.checkout()
    elif entity == 'package':
        context.package.checkout()
    elif entity == 'service':
        context.service.checkout()
    else:
        assert False, 'Unknown entity param'


@behave.then(u'I am checked out')
def step_impl(context):
    entity = context.table.headings[0]
    if entity == 'project':
        assert context.dl.projects.get().id == context.project.id
    elif entity == 'dataset':
        assert context.project.datasets.get().id == context.dataset.id
    elif entity == 'package':
        assert context.project.packages.get().id == context.package.id
    elif entity == 'service':
        assert context.project.services.get().id == context.service.id
    else:
        assert False, 'Unknown entity param'


@behave.given(u'Feature: I pack to project directory in "{package_codebase}"')
def step_impl(context, package_codebase):
    package_codebase = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], package_codebase)
    context.codebase = context.project.codebases.pack(
        directory=package_codebase,
        name='package_codebase',
        description="some description",
    )


@behave.given(u'Feature: There is a Codebase directory with a python file in path "{code_path}"')
def step_impl(context, code_path):
    code_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], code_path)
    dirs = os.listdir(code_path)
    assert "some_code.py" in dirs
    context.feature.codebase_local_dir = code_path


@behave.given(u'Feature: I create a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.feature.dataset = context.project.datasets.create(dataset_name=dataset_name)


@behave.given(u'Get feature entities')
def step_impl(context):
    if hasattr(context.feature, 'done_setting') and context.feature.done_setting:
        for param in context.table.headings:
            if param == 'dataset':
                context.dataset = context.feature.dataset
            elif param == 'package':
                context.package = context.feature.package
            elif param == 'service':
                context.service = context.feature.service

@behave.given(u'Done setting')
def step_impl(context):
    context.feature.done_setting = True
