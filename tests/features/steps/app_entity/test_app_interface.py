import behave


@behave.when(u'I create a context.custom_installation var')
def step_impl(context):
    if hasattr(context, "dpk"):
        context.custom_installation = {"components": context.dpk.to_json().get("components", {}),
                                       "dependencies": context.dpk.to_json().get("dependencies", [])}
    else:
        raise AttributeError("'dpk' not found in 'context'")


@behave.then(u'App is not installed in the project')
def step_impl(context):
    try:
        app = context.project.apps.get(app_name=context.dpk.display_name)
        error = f"TEST FAILED: able to get app: {app.id} - {app.name}"
    except Exception:
        error = None

    assert error is None, error
