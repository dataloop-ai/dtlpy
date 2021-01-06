import behave
import os


@behave.when(u'I try to push package')
def step_impl(context):
    try:
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
            modules = context.dl.PackageModule(functions=func,
                                               name=context.dl.entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME)

        # module = context.dl.entities.DEFAULT_PACKAGE_MODULE
        package = context.project.packages.push(codebase_id=codebase_id,
                                                package_name=package_name,
                                                modules=modules,
                                                src_path=src_path)
        context.to_delete_packages_ids.append(package.id)
    except context.dl.exceptions.BadRequest as e:
        assert 'Invalid package name:' in e.message or 'Name must be at most 35 characters' in e.message
        context.name_is_valid = False
        context.error = e


@behave.when(u'I validate name "{package_name}"')
def step_impl(context, package_name):
    try:
        context.dl.packages._name_validation(package_name)
        context.name_is_valid = True
    except context.dl.exceptions.BadRequest as e:
        assert 'Invalid package name:' in e.message or 'Name must be at most 35 characters' in e.message
        context.name_is_valid = False


@behave.then(u'Name is valid')
def step_impl(context):
    return context.name_is_valid


@behave.then(u'Name is invalid')
def step_impl(context):
    return not context.name_is_valid
