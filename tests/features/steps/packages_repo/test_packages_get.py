import behave
import time

@behave.when(u'I get by name version "{version}" of package "{package_name}"')
def step_impl(context, version, package_name):
    context.package_get = context.project.packages.get(package_name=package_name,
                                               package_id=None,
                                               version=version)


@behave.when(u'I get a package by name "{package_name}"')
def step_impl(context, package_name):
    context.package_get = context.project.packages.get(package_name=package_name)


@behave.then(u'Package received equal package packet')
def step_impl(context):
    assert context.package_get.to_json() == context.package.to_json()


@behave.when(u'I get by id version "{version}" of package "{package_name}"')
def step_impl(context, version, package_name):
    context.package_get = context.project.packages.get(package_name=None,
                                               package_id=context.package.id,
                                               version=version)


@behave.then(u"I receive a list of Package objects")
def step_impl(context):
    assert isinstance(context.package_get, context.dl.entities.PagedEntities)


@behave.then(u'Package list have lenght of "{package_count}"')
def step_impl(context, package_count):
    assert len(context.package_get.items) == int(package_count)

@behave.then(u'I delete all project packages')
def step_impl(context):
    dataset = context.project.datasets.get(dataset_name='Binaries')
    dataset.delete(True, True)
    time.sleep(4)
    context.project.packages.dataset = context.project.datasets.create(dataset_name="Binaries")
