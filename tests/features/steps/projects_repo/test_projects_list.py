# coding=utf-8
"""Projects repository list function testing."""

import behave


@behave.fixture
def delete_all_projects(context):
    for item in context.dlp.projects.list():
        context.dlp.projects.delete(project_id=item.id,
                                    sure=True,
                                    really=True)


@behave.when(u'I list all projects')
def step_impl(context):
    context.list = context.dlp.projects.list()


@behave.then(u'I receive an empty list')
def step_impl(context):
    assert len(context.list) == 0


@behave.then(u'I receive a projects list of "{list_lenght}" project')
def step_impl(context, list_lenght):
    assert len(context.list) == int(list_lenght)


@behave.then(u'The project in the projects list equals the project I created')
def step_impl(context):
    assert context.list[0].to_json() == context.project.to_json()
