import behave
import time


@behave.when(u'I create driver "{driver_type}" with the name "{driver_name}"')
def step_impl(context, driver_type, driver_name):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    assert hasattr(context, "integration"), "TEST FAILED: Context has no object integration"
    try:
        context.driver_type = driver_type

        time.sleep(5)  # Wait for integration
        context.driver = context.project.drivers.create(
            name=driver_name,
            driver_type=context.driver_type,
            integration_id=context.integration.id,
            bucket_name=params.get('bucket_name', None),
            integration_type=context.integration.type,
            project_id=context.project.id,
            allow_external_delete=params.get('allow_external_delete', True),
            region=params.get('region', None),
            storage_class=params.get('storage_class', ""),
            path=params.get('path', ""))
        context.to_delete_drivers_ids.append(context.driver.id)
        context.error = None
    except Exception as e:
        context.error = e
        assert False, e


@behave.then(u'I validate driver with the name "{driver_name}" is created')
def step_impl(context, driver_name):
    try:
        context.driver = context.project.drivers.get(driver_id=context.driver.id)
        context.error = None
    except Exception as e:
        context.error = e

    assert driver_name == context.driver.name, "TEST FAILED: Expected - {}, Got - {}".format(driver_name, context.driver.name)
    assert context.driver_type == context.driver.type, "TEST FAILED: Expected - {}, Got - {}".format(context.driver_type, context.driver.type)


@behave.when(u'I create dataset "{dataset_name}" with driver entity')
def step_impl(context, dataset_name):
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, driver_id=context.driver.id, index_driver=context.index_driver_var)
    context.to_delete_datasets_ids.append(context.dataset.id)


@behave.when(u'I sync dataset in context')
def step_impl(context):
    success = context.dataset.sync()
    assert success, "TEST FAILED: Failed to sync dataset"


@behave.then(u'I validate driver dataset has "{item_count}" items')
def step_impl(context, item_count):
    num_try = 18
    interval = 10
    finished = False
    pages = None

    for i in range(num_try):
        pages = context.dataset.items.list()
        if pages.items_count == int(item_count):
            finished = True
            break
        time.sleep(interval)

    assert finished, f"TEST FAILED: Expected dataset to have {item_count} items, Actual: {pages.items_count} after {round(num_try * interval / 60, 1)} minutes"


@behave.then(u'I stream Item by path "{item_path}"')
def step_impl(context, item_path):
    try:
        item = context.dataset.items.get(filepath=item_path)
        response = context.dl.client_api.gen_request(req_type="GET", path=item.stream.split("v1")[-1])
    except Exception as e:
        context.error = e
        assert False, "TEST FAILED: Not able to stream the item"

    assert response, f"TEST FAILED: Response is empty"
