import behave
import random
import string


@behave.fixture
def delete_all_datasets(context):
    for dataset in context.project.datasets.list():

        if dataset.readonly:
            dataset.set_readonly(state=False)

        context.project.datasets.delete(dataset_id=dataset.id,
                                        sure=True,
                                        really=True)


@behave.given(u'There are no datasets')
def step_impl(context):
    behave.use_fixture(delete_all_datasets, context)
    assert len(context.project.datasets.list()) == 0
    context.dataset_count = 0


@behave.when(u'I create a dataset with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    dataset_name = 'random_dataset_{}'.format(rand_str)
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)
    context.dataset_count += 1


@behave.when(u'I create another dataset with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    dataset_name = 'random_dataset_{}'.format(rand_str)
    context.new_dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)
    context.dataset_count += 1


@behave.then(u'I create a dataset with existing recipe')
def step_impl(context):
    context.recipe_id = context.dataset.get_recipe_ids()[0]
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    dataset_name = 'random_dataset_{}'.format(rand_str)
    context.dataset2 = context.project.datasets.create(dataset_name=dataset_name, recipe_id=context.recipe_id, index_driver=context.index_driver_var)
    context.dataset_count += 1


@behave.then(u'dataset recipe is equal to the existing recipe')
def step_impl(context):
    assert context.dataset2.get_recipe_ids() == context.dataset.get_recipe_ids()


@behave.then(u'Dataset object with the same name should be exist')
def step_impl(context):
    assert isinstance(context.dataset, context.dl.entities.Dataset)


@behave.then(u'Dataset object with the same name should be exist in host')
def step_impl(context):
    dataset_get = context.project.datasets.get(dataset_name=context.dataset.name)
    assert dataset_get.to_json() == context.dataset.to_json()


@behave.when(u'When I try to create a dataset with a blank name')
def step_impl(context):
    try:
        context.project.datasets.create('', index_driver=context.index_driver_var)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Dataset with same name does not exists')
def step_impl(context):
    try:
        context.project.datasets.get(dataset_name=context.dataset.name)
    except context.dl.exceptions.NotFound:
        # good results
        pass
    except:
        # dataset still exists
        assert False


@behave.given(u'I create a dataset with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    dataset_name = 'random_dataset_{}'.format(rand_str)
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)
    context.dataset_count += 1


@behave.when(u'I try to create a dataset by the same name')
def step_impl(context):
    try:
        context.project.datasets.create(dataset_name=context.dataset.name, index_driver=context.index_driver_var)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No dataset was created')
def step_impl(context):
    assert len(context.project.datasets.list()) == context.dataset_count
