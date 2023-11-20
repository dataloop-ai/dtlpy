import behave
import time
import random


@behave.given('I create a dataset by the name of "{dataset_name}" in the project')
def step_impl(context, dataset_name):
    if hasattr(context.feature, 'dataloop_feature_dataset'):
        context.dataset = context.feature.dataloop_feature_dataset
    else:
        num = random.randint(10000, 100000)
        dataset_name = 'to-delete-test-{}_{}'.format(str(num), dataset_name)
        context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)
        context.feature.dataloop_feature_dataset = context.dataset
        time.sleep(5)

    context.dataset_name = dataset_name


@behave.when('I call datasets.clone using dataset.id')
def step_imp(context):
    context.clone_dataset = context.project.datasets.clone(dataset_id=context.dataset.id, dst_dataset_id=context.new_dataset.id)
