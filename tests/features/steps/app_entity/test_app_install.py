import json
import os
import random
from .. import fixtures
import behave


@behave.given(u'I have an app entity from "{path}"')
@behave.when(u'I have an app entity from "{path}"')
def step_impl(context, path):
    json_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
    with open(json_path) as f:
        data = json.load(f)

    # Update service runner image to latest dtlpy version if exists
    val = fixtures.access_nested_dictionary_key(data, ['components', 'services', 'versions', 'dtlpy'])
    if val:
        data['components']['services'][0]['versions'].update({"dtlpy": context.dl.__version__})

    # Update service runner image to latest dtlpy version if exists
    val = fixtures.access_nested_dictionary_key(data, ['components', 'services', 'runtime', 'runnerImage'])
    if val:
        data['components']['services'][0]['runtime'].update(
            {"runnerImage": f"dataloop_runner-cpu/main:{context.dl.__version__}.latest"})

    context.dpk = context.dl.entities.Dpk.from_json(_json=data, client_api=context.project._client_api,
                                                    project=context.project)


@behave.given(u'publish the app')
def step_impl(context):
    context.dpk.name = context.dpk.name + str(random.randint(10000, 1000000))
    context.dpk = context.dpk.publish()
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.append(context.dpk)
    else:
        context.feature.dpks = [context.dpk]


@behave.when(u'I install the app with exception')
def step_impl(context):
    try:
        app = context.dl.entities.App.from_json({}, client_api=context.project._client_api, project=context.project)
        app = context.project.apps.install(context.dpk)
        if hasattr(context.feature, 'apps'):
            context.feature.apps.append(app)
        else:
            context.feature.apps = [app]
    except Exception as e:
        context.e = e


@behave.when(u'I install the app')
@behave.given(u'I install the app')
def step_impl(context):
    context.app = context.dl.entities.App.from_json({

    }, client_api=context.project._client_api, project=context.project)
    context.app = context.project.apps.install(context.dpk)
    if hasattr(context.feature, 'apps'):
        context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]


@behave.then(u'I should get the app with the same id')
def step_impl(context):
    assert context.app.id == context.project.apps.get(app_id=context.app.id).id


@behave.then(u"I should get an exception error='{error_code}'")
def step_impl(context, error_code):
    assert context.e is not None and context.e.status_code == error_code


@behave.then(u"I validate service configuration in dpk is equal to service from app")
def step_impl(context):
    service_runtime = context.project.services.list()[0][0].runtime.to_json()
    dpk_runtime = context.dpk.components.services[0]['runtime']

    assert context.dpk.components.services[0]["name"] == context.project.services.list()[0][
        0].name, f"TEST FAILED: Field name"
    assert context.dpk.components.services[0]["moduleName"] == context.project.services.list()[0][
        0].module_name, f"TEST FAILED: Field moduleName"
    assert dpk_runtime == service_runtime, f"TEST FAILED: Field runtime"
    assert context.dpk.components.services[0]['executionTimeout'] == context.project.services.list()[0][
        0].execution_timeout, f"TEST FAILED: Field executionTimeout"
    assert context.dpk.components.services[0]['onReset'] == context.project.services.list()[0][
        0].on_reset, f"TEST FAILED: Field onReset"
    assert context.dpk.components.services[0]['runExecutionAsProcess'] == context.project.services.list()[0][
        0].run_execution_as_process, f"TEST FAILED: Field runExecutionAsProcess"


@behave.then(u'i can create pipeline function node from the app service')
def step_impl(context):
    comp = context.dl.compositions.get(composition_id=context.app.composition_id)
    s = context.dl.services.get(service_id=comp['spec'][0].get('state', {}).get('serviceId', None))
    func_node = context.dl.FunctionNode(service=s, name='test', function_name='run')
    assert func_node is not None
    assert func_node.service is not None
