# coding=utf-8
"""Projects repository get service testing."""

import behave


@behave.when(u'I get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    for i in range(7):
        try:
            context.project_get = context.dl.projects.get(project_name=context.project_name)
            break
        except context.dl.exceptions.InternalServerError:
            if i >= 6:
                raise

@behave.then(u'I get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    assert context.project_get.name == context.project_name


@behave.then(u'The project I got is equal to the one created')
def step_impl(context):
    project_json = context.project.to_json()
    if 'role' in project_json:
        project_json.pop('role')

    get_json = context.project.to_json()
    if 'role' in get_json:
        get_json.pop('role')

    assert project_json == get_json
    context.project.delete(True, True)

@behave.when(u'I get a project by the id of Project')
def step_impl(context):
    context.project_get = context.dl.projects.get(project_id=context.project.id)


@behave.when(u'I try to get a project by the name of "{project_name}"')
def step_impl(context, project_name):
    try:
        for i in range(7):
            try:
                context.project_get = context.dl.projects.get(project_name=project_name)
                context.error = None
                break
            except context.dl.exceptions.InternalServerError:
                if i >= 6:
                    raise
            except context.dl.exceptions.NotFound:
                raise
    except Exception as e:
        context.error = e


@behave.when(u'I try to get a project by id')
def step_impl(context):
    try:
        context.project = context.dl.projects.get(project_id='some_id')
        context.error = None
    except Exception as e:
        context.error = e
