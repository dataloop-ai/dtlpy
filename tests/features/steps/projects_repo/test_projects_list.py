# coding=utf-8
"""Projects repository list function testing."""

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


@behave.then(u'I receive a projects list of "{list_lenght}" project')
def step_impl(context, list_lenght):
    assert len(context.list) == int(list_lenght)


@behave.then(u'The project in the projects list equals the project I created')
def step_impl(context):
    found = False
    for project in context.list:
        if project.name == context.project.name:
            found = True
            assert project.to_json() == context.project.to_json()
    assert found is True
    context.project.delete(True, True)
