# coding=utf-8
"""Projects repository get function testing."""

import behave


@behave.when(u'I get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    context.project_get = context.dlp.projects.get(project_name=project_name)


@behave.then(u'I get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    assert context.project_get.name == project_name


@behave.then(u'The project I got is equal to the one created')
def step_impl(context):
    assert context.project.to_json() == context.project_get.to_json()


@behave.when(u'I get a project by the id of Project')
def step_impl(context):
    context.project_get = context.dlp.projects.get(project_id=context.project.id)


@behave.when(u'I try to get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    try:
        context.project = context.dlp.projects.get(project_name=project_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to get a project by id')
def step_impl(context):
    try:
        context.project = context.dlp.projects.get(project_id='some_id')
        context.error = None
    except Exception as e:
        context.error = e
