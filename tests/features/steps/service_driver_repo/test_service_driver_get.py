import behave


@behave.then(u'I validate compute service driver is "{status}"')
def step_impl(context, status='created'):
    if status not in ['created', 'archived']:
        assert False, f"TEST FAILED: status should be 'created' or 'archived' but got {status}"

    f = context.dl.Filters(resource=context.dl.FiltersResource.SERVICE_DRIVER, field='context.org', values=context.project.org['id'])
    f.add(field='computeId', values=context.compute_id)
    if status == 'archived':
        f.add(field='archived', values=True)
    res  = context.dl.service_drivers.list(filters=f)
    assert res.items_count == 1, f"TEST FAILED: Expected 1 driver actual {res.items_count}"
    context.service_driver_id = res.items[0].id
    if status == 'created':
        assert context.dl.service_drivers.get(context.service_driver_id)

    if context.service_driver_id not in context.to_delete_service_drivers_ids and status == 'created':
        context.to_delete_service_drivers_ids.append(context.service_driver_id)


@behave.then(u'I get archived service driver')
def step_impl(context):
    success, response = context.dl.client_api.gen_request(
        req_type='get',
        path=f'/serviceDrivers/{context.service_driver_id}?archived=true',
    )

    if not success and response.status_code != 404:
        assert False, f"TEST FAILED: {response.message}"


@behave.when(u'I update the service driver')
def step_impl(context):
    context.service_driver = context.dl.service_drivers.get(service_driver_id=context.service_driver_id)
    if context.service_driver.metadata is None:
        context.service_driver.metadata = {}
    context.service_driver.metadata['user'] = 'test'
    context.service_driver = context.service_driver.update()

@behave.then(u'service driver should be updated')
def step_impl(context):
    assert context.service_driver.metadata['user'] == 'test'

@behave.when(u'I delete the service driver')
def step_impl(context):
    context.service_driver = context.dl.service_drivers.get(service_driver_id=context.service_driver_id)
    deleted = context.service_driver.delete()
    assert deleted

@behave.then(u'the service driver is deleted')
def step_impl(context):
    try:
        context.service_driver = context.dl.service_drivers.get(context.compute_id)
        assert False, f"TEST FAILED: Expected not found error actual {context.compute}"
    except Exception as err:
        assert 'failed to get a service driver' in str(err).lower(), f"TEST FAILED: Expected not found error actual {err}"