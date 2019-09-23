import behave
import os
import json
import tempfile
import shutil
from .. import fixtures


@behave.when(u'I push "{plugin_number}" plugin')
def step_impl(context, plugin_number):
    package_id = None
    plugin_name = None
    inputs = None
    src_path = None
    outputs = None

    params = context.table.headings
    for param in params:
        param = param.split('=')
        if param[0] == 'plugin_name':
            if param[1] != 'None':
                plugin_name = param[1]
        elif param[0] == 'src_path':
            if param[1] != 'None':
                src_path = param[1]
                src_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], src_path)
        elif param[0] == 'package_id':
            if param[1] != 'None':
                package_id = param[1]
        elif param[0] == 'inputs':
            if param[1] != 'None':
                inputs = param[1]
        elif param[0] == 'outputs':
            if param[1] != 'None':
                outputs = param[1]

    plugin = context.project.plugins.push(package_id=package_id,
                                          plugin_name=plugin_name,
                                          src_path=src_path,
                                          inputs=inputs,
                                          outputs=outputs)
    if plugin_number == 'first':
        context.first_plugin = plugin
        context.plugin = plugin
    else:
        context.second_plugin = plugin


@behave.then(u'I receive plugin entity')
def step_impl(context):
    assert 'Plugin' in str(type(context.first_plugin))


@behave.then(u'Plugin entity equals local plugin in "{path_to_compare}"')
def step_impl(context, path_to_compare):
    # get plugin local info
    path_to_compare = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], path_to_compare)
    with open(os.path.join(path_to_compare, 'plugin.json')) as f:
        plugin_json = json.load(f)
    name = plugin_json['name']
    inputs = plugin_json['inputs']
    outputs = plugin_json['outputs']

    # unpack plugin source code
    base_temp_dir = tempfile.mktemp()
    context.project.packages.unpack(package_id=context.first_plugin.packageId,
                                    local_path=base_temp_dir)
    temp_dir = os.path.join(base_temp_dir, 'dist')

    # assertions
    assert fixtures.compare_dir_recursive(path_to_compare, temp_dir)
    assert name == context.first_plugin.name
    assert inputs == context.first_plugin.inputs
    assert outputs == context.first_plugin.outputs

    shutil.rmtree(base_temp_dir)


@behave.then(u'I receive another plugin entity')
def step_impl(context):
    assert 'Plugin' in str(type(context.second_plugin))


@behave.then(u'1st plugin and 2nd plugin only differ in package id')
def step_impl(context):
    first_plugin_json = context.first_plugin.to_json()
    second_plugin_json = context.second_plugin.to_json()
    
    assert first_plugin_json.pop('packageId') != second_plugin_json.pop('packageId')
    assert first_plugin_json.pop('updatedAt') != second_plugin_json.pop('updatedAt')
    second_plugin_json['revisions'].pop(first_plugin_json['version']-1)
    assert first_plugin_json.pop('version') == second_plugin_json.pop('version') - 1
    assert first_plugin_json == second_plugin_json
