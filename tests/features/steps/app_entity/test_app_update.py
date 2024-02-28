import behave


@behave.when(u'I update the app')
def step_impl(context):
    context.app_updated = context.project.apps.update(app_id=context.app.id)


@behave.then(u'The update should success')
def step_impl(context):
    assert context.app_updated is True


@behave.when(u'I update an app')
def step_impl(context):
    if hasattr(context, "custom_installation"):
        context.app.custom_installation = context.custom_installation
    context.app.update()


@behave.when(u'I increment app dpk_version')
def step_impl(context):
    version = context.app.dpk_version.split('.')
    version[2] = str(int(version[2]) + 1)
    context.app.dpk_version = '.'.join(version)
