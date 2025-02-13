import behave


@behave.then(u'I validate compute service driver is "{status}"')
def step_impl(context, status='created'):
    if status not in ['created', 'archived']:
        assert False, f"TEST FAILED: status should be 'created' or 'archived' but got {status}"

    json_req = {"filter": {"context": {"org": context.project.org['id']}, 'computeId': context.compute_id}}
    if status == 'archived':
        json_req['filter']['archived'] = True
    success, response = context.dl.client_api.gen_request(
        req_type='post',
        path='/serviceDrivers/query',
        json_req=json_req
    )
    if not success:
        assert False, f"TEST FAILED: {response.message}"
    assert response.json()[
               'totalItemsCount'] == 1, f"TEST FAILED: Expected 1 driver actual {response.json()['totalItemsCount']}"
    context.service_driver_id = response.json()['items'][0]['id']
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
