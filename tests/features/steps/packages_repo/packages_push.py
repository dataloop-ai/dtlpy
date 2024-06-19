import behave
import os
import json
import shutil
import random

from .. import fixtures


@behave.when(u'I push "{package_number}" package')
def step_impl(context, package_number):
    codebase_id = None
    package_name = None
    inputs = list()
    src_path = None
    outputs = list()
    modules = None
    package_type = 'faas'

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
                inputs = fixtures.get_package_io(params=param[1].split(','), context=context)
        elif param[0] == 'outputs':
            if param[1] != 'None':
                outputs = fixtures.get_package_io(params=param[1].split(','), context=context)
        elif param[0] == 'modules':
            if param[1] != 'None':
                modules = param[1]
        elif param[0] == 'type':
            if param[1] != 'None':
                package_type = param[1]

    modules_name = context.dl.entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME if package_type == 'faas' else 'model-adapter'
    if package_type == 'ml':
        func = [context.dl.PackageFunction(name='train_model',
                                           inputs=[context.dl.FunctionIO(name='model',
                                                                         type=context.dl.PackageInputType.MODEL),
                                                   context.dl.FunctionIO(name='cleanup',
                                                                         type=context.dl.PackageInputType.BOOLEAN)
                                                   ],
                                           outputs=[context.dl.FunctionIO(name='model',
                                                                          type=context.dl.PackageInputType.MODEL)])]
        modules = context.dl.PackageModule(functions=func,
                                           name=modules_name,
                                           init_inputs=[context.dl.FunctionIO(name='model_entity',
                                                                              type=context.dl.PackageInputType.MODEL)])
    if modules == 'no_input':
        func = [context.dl.PackageFunction()]
        modules = context.dl.PackageModule(functions=func,
                                           name=modules_name)

    elif inputs or outputs:
        func = [context.dl.PackageFunction(inputs=inputs, outputs=outputs)]
        modules = context.dl.PackageModule(functions=func,
                                           name=modules_name)
    codebase = None
    if codebase_id is not None:
        codebase = context.dl.entities.ItemCodebase(item_id=codebase_id)

    try:
        package = context.project.packages.push(
            codebase=codebase,
            package_name=package_name,
            modules=modules,
            src_path=src_path,
            package_type=package_type
        )

        context.to_delete_packages_ids.append(package.id)
        if package_number == 'first':
            context.first_package = package
            context.package = package
        else:
            context.second_package = package

        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I receive package entity')
def step_impl(context):
    assert 'Package' in str(type(context.first_package))


@behave.given(u'I create a package with secrets with entry point "{path}"')
def step_impl(context, path):
    modules = [
        context.dl.PackageModule(name='default_module',
                                 entry_point='main.py',
                                 init_inputs=[
                                     context.dl.FunctionIO(type=context.dl.PackageInputType.STRING, name="test",
                                                           value='$env(default_key)',
                                                           integration={"type": "key_value"})],
                                 functions=[
                                     context.dl.PackageFunction(
                                         inputs=[
                                             context.dl.FunctionIO(type=context.dl.PackageInputType.ITEM, name="item")],
                                         outputs=[],
                                         name='run'),
                                 ])]

    context.package = context.project.packages.push(
        package_name="secretspackage",
        src_path=os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path),
        modules=modules,
    )

    context.service = context.package.services.deploy(
        service_name=context.package.name,
        package=context.package,
        sdk_version=context.dl.__version__,
        init_input={'test': '$env(default_key)'},
        secrets=[context.integration.id]
    )


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


def compare_codebase_id(first_package, second_package):
    if first_package.codebase.item_id is not None and second_package.codebase.item_id is not None:
        return first_package.codebase.item_id != second_package.codebase.item_id
    else:
        raise Exception('Packages does not have codebase id')


@behave.then(u'1st package and 2nd package only differ in code base id')
def step_impl(context):
    assert compare_codebase_id(context.first_package, context.second_package)

    first_package_json = context.first_package.to_json()
    second_package_json = context.second_package.to_json()

    first_package_json.pop('codebase', None)
    second_package_json.pop('codebase', None)

    assert first_package_json.pop('updatedAt') != second_package_json.pop('updatedAt')
    assert int(first_package_json.pop('version').replace(".", "")) == \
           int(second_package_json.pop('version').replace(".", "")) - 1
    assert first_package_json == second_package_json


@behave.when(u'I update package')
def step_impl(context):
    context.package = context.package.update()


@behave.when(u'i update the context module from package')
def step_impl(context):
    context.module = context.package.modules[0]


@behave.then(u'I expect package version to be "{version}" and revision list size "{revision_size}"')
def step_impl(context, version, revision_size):
    package_revision_size = len(context.package.revisions)

    assert version == context.package.version, "TEST FAILED: Expect version to be {} got {}".format(version,
                                                                                                    context.package.version)
    assert int(
        revision_size) == package_revision_size, "TEST FAILED: Expect package revision size to be {} got {}".format(
        revision_size, package_revision_size)


@behave.then(u'I validate service version is "{version}"')
def step_impl(context, version):
    assert version == context.service.package_revision, "TEST FAILED: Expect version to be {} got {}".format(version,
                                                                                                             context.service.package_revision)


@behave.when(u'I add new function to package')
def step_impl(context):
    function_1 = {'name': 'run_1',
                  'description': None,
                  'input': [{'name': 'item', 'type': 'Item'}],
                  'output': [],
                  'displayIcon': ''}

    context.package.modules[0].add_function(function_1)
    context.package = context.package.update()


@behave.when(u'Add requirements "{req}" to package')
def step_impl(context, req):
    context.package.requirements = [context.dl.PackageRequirement(name=req)]
    context.package.update()


@behave.given(u'I delete dataset Binaries')
def step_impl(context):
    datasets = context.project.datasets.list()
    context.binaries_dataset_ids = list()
    for dataset in datasets:
        if dataset.name == 'Binaries':
            context.binaries_dataset_ids.append(dataset.id)
            dataset.delete(True, True)
    datasets = context.project.datasets.list()
    for dataset in datasets:
        if dataset.name == 'Binaries':
            assert False, 'Failed to delete Binaries dataset'
    context.project = context.dl.projects.get(project_id=context.project.id)
