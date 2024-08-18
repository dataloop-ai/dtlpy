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

    data = fixtures.update_dtlpy_version(data)

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
        dpk = context.published_dpk if hasattr(context, "published_dpk") else context.dpk
        app = context.dl.entities.App.from_json({}, client_api=context.project._client_api, project=context.project)
        app = context.project.apps.install(dpk)
        if hasattr(context.feature, 'apps'):
            context.feature.apps.append(app)
        else:
            context.feature.apps = [app]
    except Exception as e:
        context.error = e


@behave.when(u'I install the app')
@behave.given(u'I install the app')
@behave.when(u'I install the app with custom_installation "{flag}"')
def step_impl(context, flag="True"):
    if hasattr(context, "custom_installation") and eval(flag):
        custom_installation = context.custom_installation
    elif eval(flag):
        custom_installation = {"components": context.dpk.to_json().get("components", {}),
                               "dependencies": context.dpk.to_json().get("dependencies", [])}
    else:
        custom_installation = None

    context.app = context.dl.entities.App.from_json(
        {},
        client_api=context.project._client_api,
        project=context.project)
    dpk = context.published_dpk if hasattr(context, "published_dpk") else context.dpk
    context.app = context.project.apps.install(dpk=dpk, custom_installation=custom_installation)
    if hasattr(context.feature, 'apps'):
        context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]


@behave.when(u'I install the app without custom_installation')
def step_impl(context):
    context.app = context.dl.entities.App.from_json(
        {},
        client_api=context.project._client_api,
        project=context.project)
    dpk = context.published_dpk if hasattr(context, "published_dpk") else context.dpk
    context.app = context.project.apps.install(dpk=dpk)
    if hasattr(context.feature, 'apps'):
        context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]


@behave.when(u'I install the app with integration')
def step_impl(context):
    context.app = context.dl.entities.App.from_json(
        {},
        client_api=context.project._client_api,
        project=context.project)
    dpk = context.published_dpk if hasattr(context, "published_dpk") else context.dpk
    context.app = context.project.apps.install(dpk=dpk, integrations=[{
        "key": "nvidiaUser",
        "env": "nvidiaUser",
        "type": "key_value",
        "value": context.integration.id,
    }])
    if hasattr(context.feature, 'apps'):
        context.feature.apps.append(context.app)
    else:
        context.feature.apps = [context.app]


@behave.then(u'I should get the app with the same id')
def step_impl(context):
    assert context.app.id == context.project.apps.get(app_id=context.app.id).id


@behave.then(u"I should get an exception error='{error_code}'")
def step_impl(context, error_code):
    assert context.error is not None and context.error.status_code == error_code


@behave.then(u"I validate service configuration in dpk is equal to service from app")
def step_impl(context):
    context.dpk_service = None
    if not hasattr(context, "service"):
        raise AttributeError("Please make sure context has attr 'service'")
    service_runtime = context.service.runtime.to_json()
    for service in context.dpk.components.services:
        if service['name'] == context.service.name:
            context.dpk_service = service
            break
    assert context.dpk_service, "TEST FAILED: Failed to find dpk_service by field service name"
    dpk_runtime = context.dpk_service['runtime']
    if "dataloop_runner-cpu" not in dpk_runtime['runnerImage']:
        dpk_runtime['runnerImage'] = dpk_runtime['runnerImage'].split("/")[-1]
        service_runtime['runnerImage'] = service_runtime['runnerImage'].split("/")[-1]

    assert context.dpk_service["moduleName"] == context.service.module_name, f"TEST FAILED: Field moduleName"
    assert dpk_runtime == service_runtime, f"TEST FAILED: Field runtime"
    assert context.dpk_service[
               'executionTimeout'] == context.service.execution_timeout, f"TEST FAILED: Field executionTimeout"
    assert context.dpk_service['onReset'] == context.service.on_reset, f"TEST FAILED: Field onReset"
    assert context.dpk_service[
               'runExecutionAsProcess'] == context.service.run_execution_as_process, f"TEST FAILED: Field runExecutionAsProcess"
    assert context.dpk_service['versions']['dtlpy'] == context.service.versions['dtlpy'], \
        f"TEST FAILED: Field versions.dtlpy DPK {context.dpk.components.services[0]['versions']['dtlpy']} " \
        f"Service {context.service.versions['dtlpy']}"


@behave.then(u'i can create pipeline function node from the app service')
def step_impl(context):
    comp = context.dl.compositions.get(composition_id=context.app.composition_id)
    s = context.dl.services.get(service_id=comp['spec'][0].get('state', {}).get('serviceId', None))
    func_node = context.dl.FunctionNode(service=s, name='test', function_name='run')
    assert func_node is not None
    assert func_node.service is not None


@behave.then(u'I compare service config with dpk compute configuration for the operation "{operation}"')
@behave.then(u'I compare service config with context.compute_config_item')
def step_impl(context, operation=None):
    service = context.service
    if operation:
        model_dpk = context.dpk.components.models[0]
        compute_configs = context.dpk.components.computeConfigs
        compute_config = [item for (index, item) in enumerate(compute_configs) if
                          item["name"] == model_dpk["computeConfigs"][operation]][0]
    else:
        compute_config = context.compute_config_item
    assert compute_config["runtime"]["runnerImage"] \
           == service.runtime.runner_image, f"TEST FAILED: Field runnerImage expected {compute_config['runtime']['runnerImage']} actual on service {service.runtime.runner_image}"


@behave.then(u'The dataset component has been installed successfully')
def step_impl(context):
    comp = context.dl.compositions.get(composition_id=context.app.composition_id)
    service = context.dl.services.get(service_id=comp['datasets'][0].get('state', {}).get('serviceId', None))
    dataset = context.dl.datasets.get(dataset_id=comp["datasets"][0]["datasetId"])
    execution = context.dl.executions.get(execution_id=comp["datasets"][0]["state"]["executionId"])

    assert comp["datasets"][0]["state"]["dataset"]["id"] == comp["datasets"][0]["datasetId"]
    assert service is not None
    assert dataset is not None
    assert execution is not None
