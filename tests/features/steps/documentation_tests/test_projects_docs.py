import behave
import time
import dtlpy as dl
import random


@behave.given(u'Create a Project "{project_name}"')
def creating_a_project(context, project_name):
    import dtlpy as dl
    if dl.token_expired():
        dl.login()
    context.random_num = str(random.randint(1000, 10000))
    project_name = project_name + context.random_num
    context.project = context.dl.projects.create(project_name=project_name)

    context.to_delete_projects_ids.append(context.project.id)

@behave.when(u'Create a Project "{project_name}"')
def creating_a_project(context, project_name):
    import dtlpy as dl
    if dl.token_expired():
        dl.login()
    context.random_num = str(random.randint(1000, 10000))
    project_name = project_name + context.random_num
    context.project = context.dl.projects.create(project_name=project_name)

    context.to_delete_projects_ids.append(context.project.id)
    time.sleep(5)  # to sleep because authorization takes time

@behave.then(u'Get my projects')
def user_projects_list(context):
    assert context.dl.projects.list() != []


@behave.then(u'Get a project by name "{project_name}"')
def project_object_should_be_created(context, project_name):
    context.project = context.dl.projects.get(project_name=project_name + context.random_num)
    assert type(context.project) == context.dl.entities.Project
    assert context.project.name == project_name + context.random_num


@behave.then(u'Get a project by project ID')
def step_impl(context):
    assert context.project.id is not None

@behave.then(u'Print a Project')
def step_impl(context):
    context.project.print()


