import behave
import os
import shutil
import filecmp
import random


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


@behave.when(u'I change project name to "{new_project_name}"')
def step_impl(context, new_project_name):
    new_project_name = new_project_name + str(random.randint(10000, 100000))
    context.project.name = new_project_name
    context.project.update()
    context.new_project_name = new_project_name


@behave.then(u'Project in host has name "{new_project_name}"')
def step_impl(context, new_project_name):
    project_get = context.dl.projects.get(project_id=context.project.id)
    assert project_get.name == context.new_project_name


@behave.when(u'I use project entity to pack directory by name "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase = context.project.pack_codebase(
        directory=context.codebase_local_dir,
        name=codebase_name,
        description="some description",
    )


@behave.then(u'Project entity was deleted')
def step_impl(context):
    try:
        context.dl.projects.get(project_id=context.project.id)
        assert False
    except Exception as e:
        assert type(e) == context.dl.exceptions.NotFound
        context.project = context.dl.projects.create(context.project.name)
        context.to_delete_projects_ids.append(context.project.id)
        context.feature.dataloop_feature_project = context.project


@behave.when(u'I reclaim project')
def step_impl(context):
    context.project = context.dl.projects.get(project_id=context.project.id)


@behave.when(u'I checkout project')
def step_impl(context):
    context.project.checkout()
