import behave


@behave.when(u'I list all project packages')
def step_impl(context):
    context.packages_list = context.project.packages.list()


@behave.then(u'I receive a list of "{num_packages}" packages')
def step_impl(context, num_packages):
    assert context.packages_list.items_count == int(num_packages)
