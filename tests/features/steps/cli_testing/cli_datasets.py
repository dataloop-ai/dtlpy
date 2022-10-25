import behave
import os
import shutil


@behave.then(u'I create a dataset by the name of "{dataset_name}" in project "{project_name}"')
def step_impl(context, dataset_name, project_name):
    assert isinstance(dataset_name, str)
    project_name = project_name.replace("<random>", context.random)
    dataset_name = dataset_name.replace("<random>", context.random)
    project = context.dl.projects.get(project_name=project_name)
    project.datasets.get(dataset_name=dataset_name)


@behave.given(u'I clean folder "{dir_path}"')
def step_impl(_, dir_path):
    rel_path = os.environ['DATALOOP_TEST_ASSETS']
    dir_path = dir_path.replace("<rel_path>", rel_path)
    for item in os.listdir(dir_path):
        path = os.path.join(dir_path, item)
        if item == 'folder_keeper':
            continue
        elif os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

