import behave
import os
from .. import fixtures
import dtlpy as dl
from operator import attrgetter


@behave.when(u'I create PackageModule with params')
def step_impl(context):
    module_name = "default_module"
    init_inputs = None
    entry_point = None
    class_name = "ServiceRunner"
    functions = [dl.PackageFunction()]

    params = context.table.headings
    for param in params:
        param = param.split('=')
        if param[0] == 'name':
            if param[1] != 'None':
                module_name = param[1]
        elif param[0] == 'init_inputs':
            if param[1] != 'None':
                init_inputs = fixtures.get_package_io(params=param[1].split(','), context=context)
        elif param[0] == 'entry_point':
            if param[1] != 'None':
                entry_point = param[1]
        elif param[0] == 'class_name':
            if param[1] != 'None':
                class_name = param[1]
        elif param[0] == 'functions':
            if param[1] != 'None':
                functions = list()
                for func in eval(param[1]):
                    function_name = func.get("function_name", "run")
                    description = func.get("description", None)
                    inputs = fixtures.get_package_io(params=func['inputs'].split(','), context=context) if func.get(
                        'inputs') else []
                    outputs = fixtures.get_package_io(params=func['outputs'].split(','), context=context) if func.get(
                        'outputs') else []
                    functions.append(dl.PackageFunction(name=function_name,
                                                        inputs=inputs,
                                                        outputs=outputs,
                                                        description=description))

    context.module = dl.PackageModule(
        name=module_name,
        entry_point=entry_point,
        init_inputs=init_inputs,
        class_name=class_name,
        functions=functions
    )


@behave.when(u'I update PackageModule function "{function_index}" input "{inputs_index}" use "{source}"')
def step_impl(context, function_index, inputs_index, source):
    f_i = int(function_index) - 1
    i_i = int(inputs_index) - 1
    assert hasattr(context, "module"), "TEST FAILED: Need to have context module - use 'When I create PackageModule'"
    if source == 'module':
        source = context.module
    elif source == 'package':
        source = context.package.modules[0]

    for row in context.table:
        setattr(source.functions[f_i].inputs[i_i], row['key'], row['value'])


@behave.then(u'I verify PackageModule params')
def step_impl(context):
    if not hasattr(context, "module"):
        if hasattr(context, "package"):
            context.module = context.package.modules[0]
        else:
            assert False, "TEST FAILED: Need to have context module - use 'When I create PackageModule'"
    for row in context.table:
        att = f"context.module.{row['key']}"
        val = f"'{row['value']}'"
        exec(f"assert {att} == {val}, 'TEST FAILED: Expected '+{val}+', Actual '+{att}")
