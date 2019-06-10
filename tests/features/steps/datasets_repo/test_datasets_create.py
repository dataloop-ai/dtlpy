import behave
import time
from dtlpy import entities


@behave.fixture
def delete_all_datasets(context):
    for item in context.project.datasets.list():
        context.project.datasets.delete(dataset_id=item.id,
                                        sure=True,
                                        really=True)


@behave.given(u'There are no datasets')
def step_impl(context):
    behave.use_fixture(delete_all_datasets, context)
    assert len(context.project.datasets.list()) == 0
    context.dataset_count = 0


@behave.when(u'I create a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset = context.project.datasets.create(dataset_name=dataset_name)
    context.dataset_count += 1


@behave.then(u'Dataset object by the name of "{dataset_name}" should be exist')
def step_impl(context, dataset_name):
    assert type(context.dataset) == entities.Dataset
    assert context.dataset.name == dataset_name


@behave.then(u'Dataset by the name of "{dataset_name}" should exist in host')
def step_impl(context, dataset_name):
    dataset_get = context.project.datasets.get(dataset_name=dataset_name)
    assert dataset_get.to_json() == context.dataset.to_json()


@behave.when(u'When I try to create a dataset with a blank name')
def step_impl(context):
    try:
        context.project.datasets.create('')
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'There are no datasets')
def step_impl(context):
    assert len(context.project.datasets.list()) == 0


@behave.given(u'I create a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    context.dataset = context.project.datasets.create(dataset_name=dataset_name)
    context.dataset_count += 1


@behave.when(u'I try to create a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    try:
        context.project.datasets.create(dataset_name=dataset_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No dataset was created')
def step_impl(context):
    assert len(context.project.datasets.list()) == context.dataset_count
