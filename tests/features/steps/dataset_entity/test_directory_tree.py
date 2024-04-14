import behave
import time
import dtlpy as dl


@behave.given(u'I create a dataset named "{dataset_name}"')
def step_impl(context, dataset_name):
    assert isinstance(dataset_name, str)
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)


@behave.then(u'I get an item thumbnail response')
@behave.when(u'I get an item thumbnail response')
def step_impl(context):
    success, response = dl.client_api.gen_request(req_type='get',
                                                  path=f'/items/{context.item.id}/thumbnail')
    if not success:
        raise dl.exceptions.PlatformException(response)


@behave.then(u'dataset.directory_tree.dir_names contains "{directory_names}"')
def step_impl(context, directory_names):
    expected_names = directory_names.split(',')
    context.dataset = context.project.datasets.get(dataset_name=context.dataset.name)

    num_try = 1
    interval = 1
    finished = False

    for i in range(num_try):
        if all(name in context.dataset.directory_tree.dir_names for name in expected_names):
            finished = True
            break

        time.sleep(interval)
        context.dl.logger.warning(
            f"Step is running for {(i + 1) * 10:.2f}[s] and now Going to sleep {10:.2f}[s]")
        context.dataset = context.project.datasets.get(dataset_name=context.dataset.name)

    assert finished, f"Expected dataset to contain directories {expected_names}, Actual: {context.dataset.directory_tree.dir_names}"