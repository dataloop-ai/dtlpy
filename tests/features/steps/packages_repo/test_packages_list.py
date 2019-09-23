import behave


@behave.when(u'I list all packages')
def step_impl(context):
    context.package_list = context.project.packages.list()


@behave.then(u'I receive a list of "{package_count}" packages')
def step_impl(context, package_count):
    assert len(context.package_list.items) == int(package_count)


@behave.given(u'There are "{packages_num}" packages')
def step_impl(context, packages_num):
    context.package_list = context.project.packages.list()
    assert len(context.package_list.items) == int(packages_num)
