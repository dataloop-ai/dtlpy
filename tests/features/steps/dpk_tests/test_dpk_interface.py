import behave
import os
import json
from .. import fixtures


@behave.when(u'I get computeConfig from path "{compute_path}" named "{compute_name}"')
def step_impl(context, compute_path, compute_name):
    context.compute_config_item = None
    path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], compute_path)
    with open(path, 'r') as file:
        list_object = json.load(file)
    for compute_config in list_object:
        if compute_name == compute_config['name']:
            context.compute_config_item = compute_config
            break
    assert context.compute_config_item, f"TEST FAILED: Failed to find '{compute_name}'"
    context.compute_config_item = fixtures.update_dtlpy_version(context.compute_config_item)


@behave.when(u'I add computeConfig to dpk on "{component}" component in index "{comp_index}"')
@behave.when(u'I add computeConfig to dpk on "{component}" component in index "{comp_index}" on module in index "{module_index}"')
@behave.when(u'I add computeConfig to dpk on "{component}" component in index "{comp_index}" with operation "{operation}"')
def step_impl(context, component, comp_index, operation=None, module_index=None):
    if not hasattr(context, "compute_config_item"):
        assert False, "TEST FAILED: Please implement the step: When I get computeConfig from path '{json_path}' named '{key}'"

    if component not in ["modules", "models", "pipelineNodes", "services", "functions"]:
        assert False, f"TEST FAILED: Wrong component key '{component}' please make sure to use on of : 'modules', 'models', 'pipelineNodes', 'services', 'functions'"

    context.compute_config_obj = context.dl.entities.DpkComputeConfig.from_json(_json=context.compute_config_item)
    # Check if the dpk_obj is already in compute_configs objects
    if context.dpk.components.compute_configs or context.compute_config_obj.name not in [config.name for config in context.dpk.components.compute_configs]:
        context.dpk.components.compute_configs.append(context.compute_config_obj)

    if component != "functions":
        component_obj = getattr(context.dpk.components, component)[int(comp_index)]
    else:
        component_obj = getattr(context.dpk.components.modules[int(module_index)], component)[int(comp_index)]

    if isinstance(component_obj, dict):
        if component_obj.get('computeConfigs'):
            component_obj['computeConfigs'].update({operation: context.compute_config_obj.name})
        else:
            component_obj['computeConfigs'] = {operation: context.compute_config_obj.name}
    else:
        component_obj.compute_config = context.compute_config_obj.name


@behave.given(u'I publish a pipeline node dpk from file "{file_name}" and with code path "{code_path}"')
def step_impl(context, file_name, code_path):
    context.execute_steps(f"""
    Given I fetch the dpk from '{file_name}' file
    And I create a dataset with a random name
    When I set code path "{code_path}" to context
    And I pack directory by name "{code_path}"
    And I add codebase to dpk
    And I publish a dpk to the platform
    """)
    if not hasattr(context, 'published_dpks'):
        context.published_dpks = list()
    context.published_dpks.append(context.published_dpk)


@behave.given(u'I publish a model dpk from file "{file_name}" package "{package_name}"')
@behave.given(u'I publish a model dpk from file "{file_name}" package "{package_name}" entry point "{entry_point}" model "{model_name}" status "{status}" in index "{index}"')
@behave.given(u'I publish a model dpk from file "{file_name}" package "{package_name}" with status "{status}"')
@behave.given(u'I publish a model dpk from file "{file_name}" package "{package_name}" with status "{status}" and docker image "{docker_image}"')
def step_impl(context, file_name, package_name, entry_point='main.py', model_name='test-model', status='created', index='0', docker_image=None):
    context.execute_steps(f"""
    Given I create a dataset with a random name
    And I upload an item by the name of "test_item.jpg"
    When I upload labels to dataset
    And I upload "5" box annotation to item
    Given I fetch the dpk from '{file_name}' file
    When I create a dummy model package by the name of "{package_name}" with entry point "{entry_point}" and docker image "{docker_image}"
    And I create a model from package by the name of "{model_name}" with status "{status}" in index "{index}"
    And I publish a dpk to the platform
    """)

    if not hasattr(context, 'published_dpks'):
        context.published_dpks = list()
    context.published_dpks.append(context.published_dpk)


@behave.given(u'I fetch dpk active learning pipeline template from file with params')
def step_impl(context, entry_point='main.py', model_name='test-model', status='created', index='0'):
    params = dict()
    params['entry_point'] = entry_point
    params['model_name'] = model_name
    params['status'] = status
    params['index'] = index
    for row in context.table:
        params[row['key']] = row['value']

    if not params.get('file_name'):
        raise Exception("Please make sure to add 'file_name' to the table")
    if not params.get('package_name'):
        raise Exception("Please make sure to add 'package_name' to the table")

    context.execute_steps(f"""
    Given I create a dataset named "Upload-data"
    And I Add dataset to context.datasets
    And I create a dataset named "Ground-Truth"
    And I Add dataset to context.datasets
    When I validate global app by the name "Active Learning" is installed
    Given I fetch the dpk from 'model_dpk/modelsDpks.json' file
    When I create a dummy model package by the name of "{params['package_name']}" with entry point "{params['entry_point']}"
    And I create a model from package by the name of "{params['model_name']}" with status "{params['status']}" in index "{params['index']}"
    When I get global dpk by name "active-learning"
    Given I fetch the dpk from '{params['file_name']}' file
    """)

    if not hasattr(context, 'published_dpks'):
        context.published_dpks = list()
    context.published_dpks.append(context.dpk)
    # Make sure to publish the


@behave.when(u'I save "{dpk_obj}" in context.saved_dpk')
def step_impl(context, dpk_obj):
    try:
        context.saved_dpk = context.project.dpks.get(dpk_name=getattr(context, dpk_obj).name)
        context.error = None
    except Exception as e:
        context.error = e