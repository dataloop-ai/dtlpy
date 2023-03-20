import os
import behave
import json


@behave.when(u'I create driver "{driver_type}" with the name "{driver_name}"')
def step_impl(context, driver_type, driver_name):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    assert hasattr(context, "integration"), "TEST FAILED: Context has no object integration"
    try:
        context.driver_type = driver_type.replace('aws', 's3')

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
        context.driver = context.project.drivers.get(integrations_id=context.driver.id)
        context.error = None
    except Exception as e:
        context.error = e

    assert driver_name == context.driver.name, "TEST FAILED: Expected - {}, Got - {}".format(driver_name, context.driver.name)
    assert context.driver_type == context.driver.type, "TEST FAILED: Expected - {}, Got - {}".format(context.driver_type, context.driver.type)


