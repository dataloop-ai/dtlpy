import behave
import filecmp
import shutil
import os


@behave.given(u'There is a Package directory with a python file in path "{code_path}"')
def step_impl(context, code_path):
    code_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], code_path)
    dirs = os.listdir(code_path)
    assert "some_code.py" in dirs
    context.package_local_dir = code_path
    context.package_unpack_path = os.path.split(code_path)[-1]


@behave.given(u"I init packages with params project, dataset, client_api")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items.client_api,
    )

@behave.given(u"Project has packages repositiory")
def step_impl(context):
    context.packages = context.project.packages


@behave.given(u"I have a packages repository")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items.client_api,
    )


@behave.given(u"I init packages with params project, client_api")
def step_impl(context):
    context.packages = context.dl.repositories.Packages(
        project=context.project, client_api=context.dataset.items.client_api
    )


@behave.when(u'I pack directory by name "{package_name}"')
def step_impl(context, package_name):
    context.package = context.packages.pack(
        directory=context.package_local_dir,
        name=package_name,
        description="some description",
    )


@behave.when(u"I pack directory - nameless")
def step_impl(context):
    context.package = context.packages.pack(
        directory=context.package_local_dir
        # name="Package_name",
        # description="some description"
    )


@behave.then(u"I receive a Package object")
def step_impl(context):
    assert isinstance(context.package, context.dl.Package)


@behave.then(u'Package in host when downloaded to "{unpack_path}" equals package in path "{original_path}"')
def step_impl(context, original_path, unpack_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.packages.unpack(package_id=context.package.id, local_path=unpack_path)
    unpack_path = os.path.join(unpack_path, 'dist')
    dirs = os.listdir(unpack_path)
    if 'folder_keeper' in dirs:
        dirs.pop(dirs.index('folder_keeper'))
    assert len(os.listdir(original_path)) == len(dirs)
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(unpack_path)


@behave.then(u'Dataset by the name of "{binaries_dataset_name}" was created')
def step_impl(context, binaries_dataset_name):
    context.dataset_binaries = context.project.datasets.get(
        dataset_name=binaries_dataset_name
    )


@behave.then(u'Package in host in dataset "{dataset_name}", when downloaded to "{unpack_path}" equals package in path "{original_path}"')
def step_impl(context, original_path, dataset_name, unpack_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.packages.unpack(package_id=context.package.id, local_path=unpack_path)
    unpack_path = os.path.join(unpack_path, 'dist')
    dirs = os.listdir(unpack_path)
    if 'folder_keeper' in dirs:
        dirs.pop(dirs.index('folder_keeper'))
    assert len(os.listdir(original_path)) == len(dirs)
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(unpack_path)


@behave.then(u'There should be "{version_count}" versions of the package "{package_name}" in host')
def step_impl(context, version_count, package_name):
    package_name = os.path.split(os.path.split(context.package.filename)[0])[-1]
    package_get = context.packages.get(package_name=package_name, version="all")
    assert package_get.items_count == int(version_count)


@behave.when(u'I modify python file - (change version) in path "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    with open(file_path, "a") as f:
        f.write("#some comments")
    f.close()
