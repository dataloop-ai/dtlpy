import behave
import os
import filecmp
import shutil


@behave.given(u'I pack directory by name "{package_name}"')
def step_impl(context, package_name):
    context.package = context.packages.pack(
        directory=context.package_local_dir,
        name=package_name,
        description="some description"
    )


@behave.when(u'I unpack a package by the name of "{package_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, package_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.packages.unpack(package_name=package_name, local_path=unpack_path)
    context.unpack_path = unpack_path + "/package"


@behave.when(u'I unpack a package by the id of "{package_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, package_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.packages.unpack(package_id=context.package.id, local_path=unpack_path)
    context.unpack_path = unpack_path + "/package"


@behave.then(u'Unpacked package equal to package in "{original_path}"')
def step_impl(context, original_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    assert len(os.listdir(original_path)) == len(os.listdir(context.unpack_path))
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(context.unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(context.unpack_path)


@behave.when(u'I try to unpack a package by the name of "{package_name}" to "{unpack_path}"')
def step_impl(context, unpack_path, package_name):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.packages.unpack(package_name=package_name,
                                local_path=unpack_path)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to unpack a package by the id of "{wrong_id}" to "{unpack_path}"')
def step_impl(context, unpack_path, wrong_id):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.packages.unpack(package_id=wrong_id,
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


@behave.when(u'I unpack a package "{package_name}" version "{version}" to "{unpack_path}"')
def step_impl(context, version, package_name, unpack_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.packages.unpack(package_name=package_name,
                            local_path=unpack_path,
                            version=version)
    context.unpack_path = unpack_path + "/package"


@behave.then(u'I receive all versions in "{unpack_path}" and they are equal to versions in "{original_path}"')
def step_impl(context, unpack_path, original_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    dirs_unpack_path = os.listdir(unpack_path)
    assert len(dirs_unpack_path) == 2
    code = 'package/some_code.py'
    for dir in dirs_unpack_path:
        version_path = os.path.join(unpack_path, dir)
        code_path = os.path.join(version_path, code)
        if dir == 'v.0':
            with open(code_path, "a") as f:
                f.write("#some comments")
            f.close()
        assert filecmp.cmp(original_path, code_path)
        shutil.rmtree(version_path)


@behave.when(u'I try to unpack a package "{package_name}" version "{version}" to "{unpack_path}"')
def step_impl(context, version, package_name, unpack_path):
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    try:
        context.packages.unpack(package_name=package_name,
                                local_path=unpack_path,
                                version=version)
        context.error = None
    except Exception as e:
        context.error = e
