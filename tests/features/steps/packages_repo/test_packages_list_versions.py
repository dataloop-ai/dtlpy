import behave


@behave.when(u'I list versions of "{package_name}"')
def step_impl(context, package_name):
    context.package_version_list = context.project.packages.list_versions(package_name=package_name)


@behave.then(u'I receive a list of "{version_count}" versions')
def step_impl(context, version_count):
    assert len(context.package_version_list.items) == int(version_count)
