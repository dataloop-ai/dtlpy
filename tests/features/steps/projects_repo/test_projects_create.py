import behave
import time
import random


@behave.when(u'I try to create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    try:
        context.project = context.dl.projects.create(project_name=project_name)
        context.to_delete_projects_ids.append(context.project.id)
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    if not project_name.startswith('to-delete-test-'):
        project_name = 'to-delete-test-' + project_name
    project_name = project_name + str(random.randint(10000, 100000))
    context.project = context.dl.projects.create(project_name=project_name)
    context.to_delete_projects_ids.append(context.project.id)
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


@behave.when(u'When I try to create a project with a blank name')
def step_impl(context):
    try:
        context.project = context.dl.projects.create(project_name='')
        context.to_delete_projects_ids.append(context.project.id)
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I receive error with status code "{status_code}"')
def step_impl(context, status_code):
    if context.error.status_code == status_code or context.error.status_code == int(status_code):
        return
    assert False, f"Expected {context.error.status_code}, Actual Got {status_code}"


@behave.then(u'"{error}" exception should be raised')
def step_impl(context, error):
    assert error in str(type(context.error)), "TEST FAILED: Expected to get {}, Actual got {}".format(error, type(
        context.error))


@behave.then(u'"{error_msg}" in error message')
@behave.then(u'"{error_msg}" in error message with status code "{status_code}"')
def step_impl(context, error_msg, status_code=None):
    if status_code:
        assert status_code == context.error.status_code, f"TEST FAILED: Expected status_code: {status_code}\nActual Got {context.error.message}"
    assert error_msg in context.error.message, f"TEST FAILED: Actual msg: {context.error.message}"


@behave.then(u'Error message includes "{error_text}"')
def step_impl(context, error_text):
    assert error_text in str(context.error)
