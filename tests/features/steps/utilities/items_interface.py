import behave
import os


@behave.given(u'I upload an item in the path "{item_path}" to the dataset')
def step_impl(context, item_path):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=context.item_path)


@behave.given(u'I upload an item in the path "{item_path}" to "{dataset_name}"')
def step_impl(context, item_path, dataset_name):
    context.item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    dataset = context.dl.datasets.get(dataset_name=dataset_name)
    context.item = dataset.items.upload(local_path=context.item_path)
