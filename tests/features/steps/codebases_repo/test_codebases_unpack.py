import behave
import os
import filecmp
import shutil
from .. import fixtures


@behave.given(u'I pack directory by name "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase = context.project.codebases.pack(
        directory=context.codebase_local_dir,
        name=codebase_name,
        description="some description"
    )


@behave.when(u'I unpack a code base by the name of "{codebase_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, codebase_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.project.codebases.unpack(codebase_name=codebase_name, local_path=unpack_path)
    context.unpack_path = unpack_path


@behave.when(u'I unpack a code base by the id of "{codebase_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, codebase_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.project.codebases.unpack(codebase_id=context.codebase.id, local_path=unpack_path)
    context.unpack_path = unpack_path


@behave.then(u'Unpacked code base equal to code base in "{original_path}"')
def step_impl(context, original_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)

    equal = fixtures.compare_dir_recursive(original_path, context.unpack_path)
    assert equal
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(context.unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(context.unpack_path)


@behave.when(u'I try to unpack a code base by the name of "{codebase_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, codebase_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.project.codebases.unpack(codebase_name=codebase_name,
                                         local_path=unpack_path)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to unpack a code base by the id of "{wrong_id}" to "{unpack_path}"')
def step_impl(context, unpack_path, wrong_id):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.project.codebases.unpack(codebase_id=wrong_id,
                                         local_path=unpack_path)
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u'I modify python file - (change version) in path "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    with open(file_path, "a") as f:
        f.write("#some comments")
    f.close()


@behave.when(u'I unpack a code base "{codebase_name}" version "{version}" to "{unpack_path}"')
def step_impl(context, version, codebase_name, unpack_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.project.codebases.unpack(codebase_name=codebase_name,
                                     local_path=unpack_path,
                                     version=version)
    context.unpack_path = unpack_path


@behave.then(u'I receive all versions in "{unpack_path}" and they are equal to versions in "{original_path}"')
def step_impl(context, unpack_path, original_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    dirs_unpack_path = os.listdir(unpack_path)
    if 'folder_keeper' in dirs_unpack_path:
        dirs_unpack_path.pop(dirs_unpack_path.index('folder_keeper'))
    assert len(dirs_unpack_path) == 2
    code = 'some_code.py'
    for dir in dirs_unpack_path:
        version_path = os.path.join(unpack_path, dir)
        code_path = os.path.join(version_path, code)
        if dir == 'v.0':
            with open(code_path, "a") as f:
                f.write("#some comments")
            f.close()
        assert filecmp.cmp(original_path, code_path)
        shutil.rmtree(version_path)


@behave.when(u'I try to unpack a code base "{codebase_name}" version "{version}" to "{unpack_path}"')
def step_impl(context, version, codebase_name, unpack_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.project.codebases.unpack(codebase_name=codebase_name,
                                         local_path=unpack_path,
                                         version=version)
        context.error = None
    except Exception as e:
        context.error = e
