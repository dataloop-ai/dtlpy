import behave
import filecmp
import shutil
import os


@behave.given(u'There is a Codebase directory with a python file in path "{code_path}"')
def step_impl(context, code_path):
    code_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], code_path)
    dirs = os.listdir(code_path)
    assert "some_code.py" in dirs
    context.codebase_local_dir = code_path
    context.codebase_unpack_path = os.path.split(code_path)[-1]


@behave.given(u"I init code bases with params project, dataset, client_api")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items._client_api,
    )


@behave.given(u"Project has code bases repositiory")
def step_impl(context):
    context.codebases = context.project.codebases


@behave.given(u"I have a code bases repository")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        project=context.project,
        dataset=context.dataset,
        client_api=context.dataset.items._client_api,
    )


@behave.given(u"I init code bases with params project, client_api")
def step_impl(context):
    context.codebases = context.dl.repositories.Codebases(
        project=context.project, client_api=context.dataset.items._client_api
    )


@behave.given(u'I pack directory by name "{codebase_name}"')
@behave.when(u'I pack directory by name "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase = context.project.codebases.pack(
        directory=context.codebase_local_dir,
        name=codebase_name,
        description="some description"
    )


@behave.when(u"I pack directory - nameless")
def step_impl(context):
    context.codebase = context.project.codebases.pack(
        directory=context.codebase_local_dir
        # name="codebase_name",
        # description="some description"
    )


@behave.then(u"I receive a Codebase object")
def step_impl(context):
    assert isinstance(context.codebase, (context.dl.ItemCodebase,
                                         context.dl.FilesystemCodebase,
                                         context.dl.LocalCodebase,
                                         context.dl.GitCodebase,
                                         ))


@behave.then(u'Codebase in host when downloaded to "{unpack_path}" equals code base in path "{original_path}"')
def step_impl(context, original_path, unpack_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.project.codebases.unpack(codebase_id=context.codebase.item_id, local_path=unpack_path)
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


@behave.then(
    u'Codebase in host in dataset "{dataset_name}", when downloaded to "{unpack_path}" equals code base in path "{original_path}"')
def step_impl(context, original_path, dataset_name, unpack_path):
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.project.codebases.unpack(codebase_id=context.codebase.item_id, local_path=unpack_path)
    dirs = os.listdir(unpack_path)
    if 'folder_keeper' in dirs:
        dirs.pop(dirs.index('folder_keeper'))
    assert len(os.listdir(original_path)) == len(dirs)
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(unpack_path)


@behave.then(u'There should be "{version_count}" versions of the code base "{codebase_name}" in host')
def step_impl(context, version_count, codebase_name):
    codebase_name = os.path.split(os.path.split(context.codebase.item.filename)[0])[-1]
    codebase_get = context.project.codebases.get(codebase_name=codebase_name, version="all")
    if isinstance(codebase_get, list):
        count = len(codebase_get)
    else:
        # paged entity
        count = codebase_get.items_count

    assert count == int(version_count)


@behave.when(u'I modify python file - (change version) in path "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    with open(file_path, "a") as f:
        f.write("#some comments")
    f.close()
