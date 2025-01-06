import behave


@behave.when(u'I resume the app')
def step_impl(context):
    try:
        app = context.project.apps.get(app_id=context.app.id)
        context.app_activated = app.resume()
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'The activation should succeed')
def step_impl(context):
    assert context.error is None, f"TEST FAILED: Expected no error, Actual got {context.error}"
    assert context.app_activated is True


@behave.when(u'I pause the app')
def step_impl(context):
    try:
        app = context.project.apps.get(app_id=context.app.id)
        context.app_deactivated = app.pause()
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'The deactivation should succeed')
def step_impl(context):
    assert context.error is None, f"TEST FAILED: Expected no error, Actual got {context.error}"
    assert context.app_deactivated is True


@behave.then(u'The service is inactive')
def step_impl(context):
    assert context.service.active is False


@behave.given(u'The service is active')
@behave.then(u'The service is active')
def step_impl(context):
    assert context.service.active is True
