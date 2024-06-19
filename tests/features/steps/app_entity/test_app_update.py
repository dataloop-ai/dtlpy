import time

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


@behave.when(u'I update app auto update to "{flag}"')
def step_impl(context, flag):
    context.app.settings['autoUpdate'] = eval(flag)
    context.app.update()


@behave.when(u'I wait for app version to be updated according to dpk version')
def step_impl(context, ):
    interval = 8
    num_try = 3
    finished = False
    for i in range(num_try):
        time.sleep(interval)
        context.app = context.project.apps.get(app_id=context.app.id)
        if context.app.dpk_version == context.dpk.version:
            finished = True
            break

    assert finished, f"TEST FAILED: App version was not updated, app current version: {context.app.dpk_version}"
