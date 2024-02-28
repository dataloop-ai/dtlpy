import behave


@behave.given(u'I uninstall the app')
@behave.when(u'I uninstall the app')
@behave.then(u'I uninstall the app')
def step_impl(context):
    context.project.apps.uninstall(app_id=context.app.id)
    context.feature.apps.pop(-1)


@behave.then(u"The app shouldn't be in listed")
def step_impl(context):
    try:
        context.project.apps.get(app_id=context.app.id)
        assert False
    except Exception:
        assert True


@behave.given(u'I uninstall not existed app')
def step_impl(context):
    try:
        context.project.apps.uninstall(app_id='Hello')
        context.error = None
    except Exception as e:
        context.error = e
