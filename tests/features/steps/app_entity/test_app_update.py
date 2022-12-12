import behave


@behave.when(u'I update the app')
def step_impl(context):
    context.app_updated = context.project.apps.update(app_id=context.app.id, pause=True)


@behave.then(u'The update should success')
def step_impl(context):
    assert context.app_updated is True
