import behave


@behave.when(u'I delete a project by the name of "{project_name}"')
def step_impl(context, project_name):
    context.dlp.projects.delete(project_name=project_name,
                                sure=True,
                                really=True)
    context.project_count -= 1


@behave.then(u'There are no projects')
def step_impl(context):
    project_list = context.dlp.projects.list()
    assert len(project_list) == 0


@behave.when(u'I delete a project by the id of "{project_name}"')
def step_impl(context, project_name):
    context.dlp.projects.delete(project_name=project_name,
                                sure=True,
                                really=True)
    context.project_count -= 1


@behave.when(u'I try to delete a project by the name of "{project_name}"')
def step_impl(context, project_name):
    try:
        context.dlp.projects.delete(project_name=project_name,
                                    sure=True,
                                    really=True)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No project was deleted')
def step_impl(context):
    assert len(context.dlp.projects.list()) == context.project_count
