# coding=utf-8
"""Projects repository create function testing."""

import behave
import time
from dtlpy import entities


@behave.fixture
def delete_all_projects(context):
    for item in context.dlp.projects.list():
        context.dlp.projects.delete(project_id=item.id,
                                    sure=True,
                                    really=True)


@behave.given('There are no projects')
def there_are_no_projects(context):
    """There are no projects."""
    behave.use_fixture(delete_all_projects, context)
    context.project_count = 0


@behave.when('I try to create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    """Creating a project."""
    try:
        context.project = context.dlp.projects.create(project_name=project_name)
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.when('I create a project by the name of "{project_name}"')
def creating_a_project(context, project_name):
    """Creating a project."""
    context.project = context.dlp.projects.create(project_name=project_name)
    time.sleep(5)  # to sleep because authorization takes time
    context.project_count += 1


@behave.then(u'Project object by the name of "{project_name}" should be created')
def project_object_should_be_created(context, project_name):
    """Project object should be created."""
    assert type(context.project) == entities.Project
    assert context.project.name == 'Project'


@behave.then('Project should exist in host')
def project_should_exist_in_host(context):
    """Project should exist in host."""
    project_get = context.dlp.projects.get(project_name='Project')
    assert project_get.to_json() == context.project.to_json()


@behave.when(u'When I try to create a project with a blank name')
def step_impl(context):
    try:
        context.project = context.dlp.projects.create(project_name='')
        time.sleep(5)  # to sleep because authorization takes time
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'"{error}" exception should be raised')
def step_impl(context, error):
    print(error)
    print(context.error)
    print(str(type(context.error)))
    assert error in str(type(context.error))


@behave.given('I create a project by the name of "{project_name}"')
def step_impl(context, project_name):
    context.project = context.dlp.projects.create(project_name=project_name)
    time.sleep(5)  # to sleep because authorization takes time
    context.project_count = len(context.dlp.projects.list())


@behave.then('No project was created')
def project_should_exist_in_host(context):
    """No project was created."""
    assert len(context.dlp.projects.list()) == context.project_count


@behave.then(u'Error message includes "{error_text}"')
def step_impl(context, error_text):
    assert error_text in str(context.error)
