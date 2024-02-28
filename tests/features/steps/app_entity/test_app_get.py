import behave
import dictdiffer


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
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I get the app without parameters')
def step_impl(context):
    try:
        context.project.apps.get()
        context.error = None
    except Exception as e:
        context.error = e


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


@behave.when(u'I validate global app by the name "{app_name}" is installed')
def step_impl(context, app_name):
    try:
        filters = context.dl.Filters(field='name',
                                     values=app_name,
                                     resource=context.dl.FiltersResource.APP,
                                     use_defaults=False)
        filters.add(field='scope', values='system')
        apps = context.dl.apps.list(filters=filters)
        if len(apps) == 0:
            raise Exception(f"App {app_name} is not installed")
        elif len(apps) > 1:
            raise Exception(f"More than one app with name {app_name} is installed")
        else:
            context.app = apps[0]
    except Exception as e:
        raise e


@behave.Then(u'I validate app.custom_installation is equal to published.dpk components')
def step_impl(context):
    if context.app.custom_installation['components'] == context.published_dpk.to_json()['components']:
        assert True
    else:
        assert False, f"TEST FAILED: {list(dictdiffer.diff(context.app.custom_installation['components'], context.published_dpk.to_json()['components']))}"
