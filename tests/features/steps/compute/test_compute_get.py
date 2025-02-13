import behave


@behave.when(u'I get compute from the compute list by the name')
@behave.when(u'I get compute from the compute list by the name with archived "{archived}"')
def step_impl(context, archived=None):
    json_req = {
        "filter": {"context": {"org": context.project.org['id']}, 'name': context.json_object['config']['name']}}
    if archived:
        json_req['filter']['archived'] = True
    success, response = context.dl.client_api.gen_request(
        req_type='post',
        path='/compute/query',
        json_req=json_req
    )

    if not success:
        assert False, f"TEST FAILED: {response.message}"

    assert response.json()[
               'totalItemsCount'] == 1, f"TEST FAILED: Expected 1 driver actual {response.json()['totalItemsCount']}"

    context.compute_id = response.json()['items'][0]['id']

    if not archived:
        context.compute = context.dl.computes.get(context.compute_id)

        if context.compute_id not in context.to_delete_computes_ids:
            context.to_delete_computes_ids.append(context.compute_id)
