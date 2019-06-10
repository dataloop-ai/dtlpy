import behave


@behave.when(u'I list all packages')
def step_impl(context):
    context.package_list = context.packages.list()


@behave.then(u'I receive a list of "{package_count}" packages')
def step_impl(context, package_count):
    assert len(context.package_list.items) == int(package_count)
