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
