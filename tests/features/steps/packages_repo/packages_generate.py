import behave
import os
import shutil
from .. import fixtures


@behave.given(u'Directory "{dir_path}" is empty')
def step_impl(context, dir_path):

    dir_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], dir_path)

    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    for item in os.listdir(dir_path):
        if item == 'folder_keeper':
            continue
        elif os.path.isdir(os.path.join(dir_path, item)):
            shutil.rmtree(os.path.join(dir_path, item))
        elif os.path.isfile(os.path.join(dir_path, item)):
            os.remove(os.path.join(dir_path, item))
    content = [item for item in os.listdir(dir_path) if item != 'folder_keeper']

    assert not content


@behave.when(u'I generate package by the name of "{package_name}" to "{src_path}"')
def step_impl(context, package_name, src_path):
    if package_name == 'None':
        package_name = None

    if src_path == 'None':
        src_path = None
    else:
        src_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], src_path)

    if src_path is not None:
        if not os.path.isdir(src_path):
            os.mkdir(src_path)

    context.project.packages.generate(name=package_name, src_path=src_path)


@behave.then(u'Package local files in "{generated_path}" equal package local files in '
             u'"{to_compare_path}"')
def step_impl(context, generated_path, to_compare_path):

    generated_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], generated_path)
    to_compare_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], to_compare_path)

    assert fixtures.compare_dir_recursive(generated_path, to_compare_path)


@behave.given(u'cwd is "{cwd}"')
def step_impl(context, cwd):
    context.original_cwd = os.getcwd()
    cwd = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], cwd)
    os.chdir(cwd)


@behave.when(u'cwd goes back to original')
def step_impl(context):
    os.chdir(context.original_cwd)
