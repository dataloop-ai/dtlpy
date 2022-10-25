# coding=utf-8
"""Projects repository list service testing."""

import behave


@behave.when(u'I list all projects')
def step_impl(context):
    for i in range(7):
        try:
            context.list = context.dl.projects.list()
            break
        except context.dl.exceptions.InternalServerError:
            if i >= 6:
                raise
        


@behave.then(u'I receive an empty list')
def step_impl(context):
    assert len(context.list) == 0


@behave.then(u'I receive a projects list of "{list_length}" project')
def step_impl(context, list_length):
    assert len(context.list) == int(list_length)


@behave.then(u'The project in the projects list equals the project I created')
def step_impl(context):
    found = False
    for project in context.list:
        if project.name == context.project.name:
            found = True
            list_json = project.to_json()
            project_json = context.project.to_json()
            list_json.pop('role', None)
            project_json.pop('role', None)
            list_json.pop('isBlocked', None)
            project_json.pop('isBlocked', None)
            assert list_json == project_json
    assert found is True
