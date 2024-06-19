import behave


@behave.when(u'I get package by the name of "{package_name}"')
def step_impl(context, package_name):
    context.package_get = context.project.packages.get(package_name=package_name)


@behave.when(u'get global model package')
@behave.given(u'get global model package')
def step_impl(context):
    package_filter = context.dl.Filters(field='name', values='testmodel', use_defaults=False,
                                        resource=context.dl.FiltersResource.PACKAGE)
    context.package = context.dl.packages.list(filters=package_filter).items[0]


@behave.when(u'I get package by id')
def step_impl(context):
    context.package_get = context.project.packages.get(package_id=context.package.id)


@behave.then(u'I get a package entity')
def step_impl(context):
    assert 'Package' in str(type(context.package_get))


@behave.then(u'It is equal to package created')
def step_impl(context):
    assert context.package.to_json() == context.package_get.to_json()
