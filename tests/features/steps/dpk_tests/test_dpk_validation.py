import behave
import dtlpy as dl


def recusive_dependencies(context, dpk, dependencies: list = None):
    if not dependencies:
        dependencies = []
    dependencies.append(dpk.name)
    if dpk.dependencies:
        for dep in dpk.dependencies:
            dpk = context.dl.dpks.get(dpk_name=dep['name'])
            recusive_dependencies(context, dpk, dependencies)
    return dependencies


@behave.then(u'I validate app dependencies are installed')
def step_impl(context):
    if not hasattr(context, "published_dpk"):
        raise AttributeError("Please make sure context has attr 'published_dpk'")
    dependencies_name = recusive_dependencies(context, context.published_dpk, [])
    filters = dl.Filters(resource='apps')
    filters.custom_filter = {"filter": {"$or": [{"projectId": context.project.id}, {"scope": "system"}]}}
    context.apps_list = context.project.apps.list(filters=filters).items
    apps_dpk_names = [app.dpk_name for app in context.apps_list]
    for app_name in dependencies_name:
        if app_name not in apps_dpk_names:
            assert False, f"App '{app_name}' was not installed"


@behave.then(u'I validate dpk dependencies have "{ref_relation}" relation refs')
@behave.then(u'I validate dpk dependencies have "{ref_relation}" relation refs "{flag}"')
def step_impl(context, ref_relation, flag=None):
    if not hasattr(context, "dpks_names"):
        raise AttributeError("Please make sure context has attr 'dpks_names'")
    for dpk_name in context.dpks_names:
        try:
            dpk = context.project.dpks.get(dpk_name=dpk_name['name'])
            for refs in dpk.metadata['system']['refs']:
                if refs['type'] == 'dpk' and refs['metadata']['relation'] == ref_relation:
                    dpk_name['flag'] = True
                elif flag:
                    # Refs has different ref_relation and flag only is on
                    assert False, f"DPK '{dpk_name['name']}' Should have only '{ref_relation}' field, Actual: {refs['metadata']['relation']}"

        except dl.exceptions.NotFound:
            assert False, f"DPK {dpk_name} was not installed"

    for flag_dpk in context.dpks_names:
        assert flag_dpk['flag'], f"App '{flag_dpk['name']}' missing '{ref_relation}' field"


@behave.then(u'I validate app dependencies have "{ref_relation}" relation refs')
@behave.then(u'I validate app dependencies have "{ref_relation}" relation refs "{flag}"')
def step_impl(context, ref_relation, flag=None):
    apps_names = [{"name": dependency['name'], "flag": False} for dependency in context.published_dpk.dependencies]
    for app_name in apps_names:
        try:
            filters = dl.Filters(resource='apps')
            filters.add(field='dpkName', values=app_name['name'])
            app = context.project.apps.list(filters=filters).items[0]
            for refs in app.metadata['system']['refs']:
                if refs['type'] == 'app' and refs['metadata']['relation'] == ref_relation:
                    app_name['flag'] = True
                elif flag:
                    # Refs has different ref_relation and flag only is on
                    assert False, f"App '{app_name['name']}' Should have only '{ref_relation}' field, Actual: {refs['metadata']['relation']}"

        except dl.exceptions.NotFound:
            assert False, f"App '{app_name}' was not installed"

    for flag_app in apps_names:
        assert flag_app['flag'], f"App {flag_app['name']} missing {ref_relation} field"


@behave.then(u'I validate app dependencies not have "{ref_relation}" relation refs')
def step_impl(context, ref_relation):
    apps_names = [{"name": dependency['name'], "flag": False} for dependency in context.published_dpk.dependencies]
    for app_name in apps_names:
        try:
            filters = dl.Filters(resource='apps')
            filters.add(field='dpkName', values=app_name['name'])
            context.app = context.project.apps.list(filters=filters).items[0]
            for refs in context.app.metadata['system']['refs']:
                if refs['type'] == 'app' and refs['id'] == context.app.id and refs['metadata']['relation'] == ref_relation:
                    assert False, f"App '{app_name['name']}' Should not have '{ref_relation}' field"

        except dl.exceptions.NotFound:
            assert False, f"App '{app_name}' was not installed"


@behave.then(u'I validate dpk dependencies not have "{ref_relation}" relation refs')
def step_impl(context, ref_relation):
    if not hasattr(context, "dpks_names"):
        raise AttributeError("Please make sure context has attr 'dpks_names'")

    for dpk_name in context.dpks_names:
        try:
            dpk = context.project.dpks.get(dpk_name=dpk_name['name'])
            for refs in dpk.metadata['system']['refs']:
                if refs['type'] == 'dpk' and refs['id'] == context.published_dpk.id and refs['metadata']['relation'] == ref_relation:
                    assert False, f"DPK '{dpk_name['name']}' Should not have '{ref_relation}' field"

        except dl.exceptions.NotFound:
            assert False, f"DPK '{dpk_name}' was not installed"


@behave.then(u'I validate app dependencies not installed')
def step_impl(context):
    apps_names = [{"name": dependency['name'], "flag": False} for dependency in context.published_dpk.dependencies]
    for app_name in apps_names:
        filters = dl.Filters(resource='apps')
        filters.add(field='dpkName', values=app_name['name'])
        if context.project.apps.list(filters=filters).items:
            assert False, f"App '{app_name['name']}' Should not be installed"


@behave.then(u'I validate the context.model has the attribute "{key}" with value "{val}"')
def step_impl(context, key, val):
    if "metadata" in key:
        last_key = key.split('.')[-1]
        if "system" in key:
            assert context.model.metadata['system'][last_key] == eval(val), f"TEST FAILED: Expected: {val} , Actual : {context.model.metadata['system'][last_key]}"
        else:
            assert context.model.metadata[last_key] == eval(val), f"TEST FAILED: Expected: {val} , Actual : {context.model.metadata[last_key]}"
    else:
        assert getattr(context.model, key) == eval(val), f"TEST FAILED: Expected: {val} , Actual : {getattr(context.model, key)}"
