import behave
import os
import shutil
import filecmp


@behave.when(u'I list project entity datasets')
def step_impl(context):
    context.dataset_list = context.project.list_datasets()


@behave.when(u'I get project entity dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset_get = context.project.get_dataset(dataset_name=dataset_name)


@behave.when(u'I create by project entity a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset = context.project.create_dataset(dataset_name)
    context.dataset_count += 1


@behave.when(u'I delete a project entity')
def step_impl(context):
    context.project.delete(sure=True,
                           really=True)
    context.project_count -= 1


@behave.when(u'I change project name to "{new_project_name}"')
def step_impl(context, new_project_name):
    context.project.name = new_project_name
    context.project.update()


@behave.then(u'Project in host has name "{new_project_name}"')
def step_impl(context, new_project_name):
    project_get = context.dlp.projects.get(project_id=context.project.id)
    assert project_get.name == new_project_name


@behave.when(u'I use project entity to pack directory by name "{package_name}"')
def step_impl(context, package_name):
    context.package = context.project.pack_package(
        directory=context.package_local_dir,
        name=package_name,
        description="some description",
    )


@behave.then(u'ent - Package in host in dataset "{dataset_name}" equals package in path "{original_path}"')
def step_impl(context, original_path, dataset_name):
    unpack_path = "package_unpack"
    original_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], original_path)
    unpack_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], unpack_path)
    context.package.unpack(local_path=unpack_path)
    unpack_path = unpack_path + "/package"
    assert len(os.listdir(original_path)) == len(os.listdir(unpack_path))
    for file in os.listdir(original_path):
        origin = os.path.join(original_path, file)
        unpack = os.path.join(unpack_path, file)
        assert filecmp.cmp(origin, unpack)
    shutil.rmtree(unpack_path)
