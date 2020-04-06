import behave
import os
import json
import tempfile
import shutil
from .. import fixtures
import logging
import random


@behave.when(u'I push "{package_number}" package')
def step_impl(context, package_number):
    codebase_id = None
    package_name = None
    inputs = None
    src_path = None
    outputs = None
    modules = None

    params = context.table.headings
    for param in params:
        param = param.split('=')
        if param[0] == 'package_name':
            if param[1] != 'None':
                package_name = param[1]
        elif param[0] == 'src_path':
            if param[1] != 'None':
                src_path = param[1]
                src_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], src_path)
        elif param[0] == 'codebase_id':
            if param[1] != 'None':
                codebase_id = param[1]
        elif param[0] == 'inputs':
            if param[1] != 'None':
                inputs = param[1]
        elif param[0] == 'outputs':
            if param[1] != 'None':
                outputs = param[1]
        elif param[0] == 'modules':
            if param[1] != 'None':
                modules = param[1]

    if modules == 'no_input':
        func = context.dl.PackageFunction()
        modules = context.dl.PackageModule(functions=func, name=context.dl.entities.DEFAULT_PACKAGE_MODULE_NAME)

    # module = context.dl.entities.DEFAULT_PACKAGE_MODULE
    package = context.project.packages.push(codebase_id=codebase_id,
                                            package_name=package_name,
                                            modules=modules,
                                            src_path=src_path)
    context.to_delete_packages_ids.append(package.id)
    if package_number == 'first':
        context.first_package = package
        context.package = package
    else:
        context.second_package = package


@behave.then(u'I receive package entity')
def step_impl(context):
    assert 'Package' in str(type(context.first_package))


@behave.then(u'Package entity equals local package in "{path_to_compare}"')
def step_impl(context, path_to_compare):
    # get package local info
    path_to_compare = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], path_to_compare)
    with open(os.path.join(path_to_compare, 'package.json')) as f:
        package_json = json.load(f)
    name = package_json['name']
    inputs = package_json['modules'][0]['functions'][0]['input']
    outputs = package_json['modules'][0]['functions'][0]['output']

    # unpack package source code
    # base_temp_dir = tempfile.mktemp()
    base_temp_dir = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], 'temp_{}'.format(str(random.randrange(0, 1000))))
    if not os.path.isdir(base_temp_dir):
        os.mkdir(base_temp_dir)

    context.project.codebases.unpack(codebase_id=context.first_package.codebase_id,
                                     local_path=base_temp_dir)

    # assertions
    assert fixtures.compare_dir_recursive(path_to_compare, base_temp_dir)
    assert name == context.first_package.name
    assert inputs == [_io.to_json() for _io in context.first_package.modules[0].functions[0].inputs]
    assert outputs == [_io.to_json() for _io in context.first_package.modules[0].functions[0].outputs]

    shutil.rmtree(base_temp_dir)


@behave.then(u'I receive another package entity')
def step_impl(context):
    assert 'Package' in str(type(context.second_package))


@behave.then(u'1st package and 2nd package only differ in code base id')
def step_impl(context):
    first_package_json = context.first_package.to_json()
    second_package_json = context.second_package.to_json()

    assert first_package_json.pop('codebaseId') != second_package_json.pop('codebaseId')
    assert first_package_json.pop('updatedAt') != second_package_json.pop('updatedAt')
    second_package_json['revisions'].pop(first_package_json['version'] - 1)
    assert first_package_json.pop('version') == second_package_json.pop('version') - 1
    assert first_package_json == second_package_json
