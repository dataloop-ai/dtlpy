import behave


@behave.when(u'I get the app by name')
def step_impl(context):
    context.web_app = context.project.apps.get(app_name=context.app.name)


@behave.when(u'I get the app by id')
def step_impl(context):
    context.web_app = context.project.apps.get(app_id=context.app.id)


@behave.when(u'I get the app with invalid id')
def step_impl(context):
    try:
        context.project.apps.get(app_id="Hola")
    except Exception as e:
        context.e = e


@behave.when(u'I get the app without parameters')
def step_impl(context):
    try:
        context.project.apps.get()
    except Exception as e:
        context.e = e


@behave.then(u'I should get identical results as the json')
def step_impl(context):
    assert context.app.to_json() == context.web_app.to_json()


@behave.when(u'I get app by name "{app_name}"')
def step_impl(context, app_name):
    context.app = context.project.apps.get(app_name=app_name)


@behave.when(u'I add app to context.feature.apps')
def step_impl(context):
    if hasattr(context.feature, "apps"):
        if context.app.id not in [app.id for app in context.feature.apps]:
            context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]

