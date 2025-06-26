import behave


@behave.given(u'I uninstall the app')
@behave.when(u'I uninstall the app')
@behave.then(u'I uninstall the app')
def step_impl(context):
    context.project.apps.uninstall(app_id=context.app.id)
    context.feature.apps.pop(-1)


@behave.then(u'I validate dpk not have refs')
def step_impl(context):
    context.dpk = context.dl.dpks.get(dpk_id=context.dpk.id)
    assert not context.dpk.metadata.get('system', {}).get('refs', {}), "Dpk still has refs: {}".format(context.dpk.metadata.get('system', {}).get('refs', {}))

@behave.then(u'I validate app not have refs')
def step_impl(context):
    context.app = context.dl.apps.get(app_id=context.app.id)
    assert not context.app.metadata.get('system', {}).get('refs', {}), "App still has refs: {}".format(context.app.metadata.get('system', {}).get('refs', {}))

@behave.then(u'I validate app have refs')
def step_impl(context):
    context.app = context.dl.apps.get(app_id=context.app.id)
    assert context.app.metadata.get('system', {}).get('refs', None), "App refs is None: {}".format(context.app.metadata.get('system', {}).get('refs', None))

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
