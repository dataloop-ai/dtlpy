import behave
import time


@behave.when(u'I get by name version "{version}" of code base "{codebase_name}"')
def step_impl(context, version, codebase_name):
    context.codebase_get = context.project.codebases.get(codebase_name=codebase_name,
                                                         codebase_id=None,
                                                         version=version)


@behave.when(u'I get a code base by name "{codebase_name}"')
def step_impl(context, codebase_name):
    context.codebase_get = context.project.codebases.get(codebase_name=codebase_name)


@behave.then(u'Codebase received equal code base packet')
def step_impl(context):
    assert context.codebase_get.to_json() == context.codebase.to_json()


@behave.when(u'I get by id version "{version}" of code base "{codebase_name}"')
def step_impl(context, version, codebase_name):
    context.codebase_get = context.project.codebases.get(
        codebase_name=None,
        codebase_id=context.codebase.item_id,
        version=version
    )


@behave.then(u"I receive a list of Codebase objects")
def step_impl(context):
    assert isinstance(context.codebase_get, list)


@behave.then(u'Codebase list have length of "{codebase_count}"')
def step_impl(context, codebase_count):
    assert len(context.codebase_get) == int(codebase_count)


@behave.then(u'I delete all project code bases')
def step_impl(context):
    dataset = context.project.datasets.get(dataset_name='Binaries')
    dataset.delete(True, True)
    time.sleep(4)
    context.project.codebases.dataset = context.project.datasets.create(dataset_name="Binaries", index_driver=context.index_driver_var)
