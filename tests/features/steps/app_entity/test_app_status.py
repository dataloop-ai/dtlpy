import behave


@behave.when(u'I resume the app')
def step_impl(context):
    try:
        context.app_activated = context.project.apps.resume(app_id=context.app.id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'The activation should succeed')
def step_impl(context):
    assert context.app_activated is True


@behave.when(u'I pause the app')
def step_impl(context):
    try:
        context.app_deactivated = context.project.apps.pause(app_id=context.app.id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'The deactivation should succeed')
def step_impl(context):
    assert context.app_deactivated is True


@behave.then(u'The service is inactive')
def step_impl(context):
    assert context.service.active is False


@behave.given(u'The service is active')
@behave.then(u'The service is active')
def step_impl(context):
    assert context.service.active is True
