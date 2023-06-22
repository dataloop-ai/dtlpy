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
