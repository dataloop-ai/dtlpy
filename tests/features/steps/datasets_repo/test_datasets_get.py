import behave
from dtlpy import entities


@behave.when(u'I get a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset_get = context.project.datasets.get(dataset_name=dataset_name)


@behave.then(u'I get a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    assert type(context.dataset_get) == entities.Dataset
    assert context.dataset_get.name == dataset_name


@behave.then(u'The dataset I got is equal to the one created')
def step_impl(context):
    assert context.dataset.to_json() == context.dataset_get.to_json()


@behave.when(u'I get a dataset by the id of the dataset "Dataset"')
def step_impl(context):
    context.dataset_get = context.project.datasets.get(dataset_id=context.dataset.id)


@behave.when(u'I try to get a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    try:
        context.project = context.project.datasets.get(dataset_name=dataset_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I try to get a dataset by id')
def step_impl(context):
    try:
        context.project = context.project.datasets.get(dataset_id='some_ID')
        context.error = None
    except Exception as e:
        context.error = e
