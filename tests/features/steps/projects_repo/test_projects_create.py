import behave
import time
import random


@behave.when(u'I try to create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    try:
        context.project = context.dl.projects.create(project_name=context.project_name)
        context.to_delete_projects_ids.append(context.project.id)
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    project_name = project_name + str(random.randint(10000, 100000))
    context.project = context.dl.projects.create(project_name=project_name)
    context.to_delete_projects_ids.append(context.project.id)
    time.sleep(5)  # to sleep because authorization takes time
    context.project_name = project_name


@behave.then(u'Project object by the name of "{project_name}" should be created')
def project_object_should_be_created(context, project_name):
    assert type(context.project) == context.dl.entities.Project
    assert context.project.name == context.project_name


@behave.then(u'Project should exist in host by the name of "{project_name}"')
def project_should_exist_in_host(context, project_name):
    project_get = context.dl.projects.get(project_id=context.project.id)

    list_json = project_get.to_json()
    project_json = context.project.to_json()
    list_json.pop('role')
    project_json.pop('role')

    assert list_json == project_json
    context.project.delete(True, True)


@behave.when(u'When I try to create a project with a blank name')
def step_impl(context):
    try:
        context.project = context.dl.projects.create(project_name='')
        context.to_delete_projects_ids.append(context.project.id)
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'"{error}" exception should be raised')
def step_impl(context, error):
    assert error in str(type(context.error))


@behave.given(u'I create a project by the name of "{project_name}"')
def step_impl(context, project_name):
    project_name = project_name + str(random.randint(10000, 100000))
    context.project = context.dl.projects.create(project_name=project_name)
    context.to_delete_projects_ids.append(context.project.id)
    time.sleep(5)  # to sleep because authorization takes time
    context.project_name = project_name


@behave.then(u'Error message includes "{error_text}"')
def step_impl(context, error_text):
    assert error_text in str(context.error)
    context.project.delete(True, True)

