import behave


@behave.when(u'I delete a project by the name of "{project_name}"')
def step_impl(context, project_name):
    for i in range(7):
        try:
            context.dl.projects.delete(project_name=context.project_name,
                                        sure=True,
                                        really=True)
            break
        except context.dl.exceptions.InternalServerError:
            if i == 6:
                raise


@behave.when(u'I delete a project by the id of "{project_name}"')
def step_impl(context, project_name):
    context.dl.projects.delete(project_id=context.project.id,
                                sure=True,
                                really=True)


@behave.when(u'I try to delete a project by the name of "{project_name}"')
def step_impl(context, project_name):
    try:
        for i in range(7):
            try:
                context.dl.projects.delete(project_name=project_name,
                                            sure=True,
                                            really=True)
                context.error = None
                break
            except context.dl.exceptions.InternalServerError:
                if i >= 6:
                    raise
            except context.dl.exceptions.NotFound:
                raise
    except Exception as e:
        context.error = e


@behave.then(u'There are no projects by the name of "{project_name}"')
def step_impl(context, project_name):
    try:
        project = None
        project = context.dl.get(project_name=context.project_name)
    except:
        assert project is None