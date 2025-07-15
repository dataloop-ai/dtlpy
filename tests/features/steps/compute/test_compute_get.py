import behave


@behave.when(u'I get compute from the compute list by the name')
@behave.when(u'I get compute from the compute list by the name with archived "{archived}"')
def step_impl(context, archived=None):
    f = context.dl.Filters(resource=context.dl.FiltersResource.COMPUTE, field='context.org',
                           values=context.project.org['id'])
    f.add(field='name', values=context.json_object['config']['name'])
    if archived == 'True':
        f.add(field='archived', values=True)
    res = context.dl.computes.list(filters=f)


    assert res.items_count == 1, f"TEST FAILED: Expected 1 driver actual {res.items_count}"

    context.compute_id = res.items[0].id

    if not archived:
        context.compute = context.dl.computes.get(context.compute_id)

        if context.compute_id not in context.to_delete_computes_ids:
            context.to_delete_computes_ids.append(context.compute_id)


@behave.when(u'I update the compute')
def step_impl(context):
    context.compute = context.dl.computes.get(context.compute_id)
    context.compute.metadata['user'] = 'test'
    context.compute = context.compute.update()

@behave.then(u'compute should be updated')
def step_impl(context):
    assert context.compute.metadata['user'] == 'test'

@behave.when(u'I delete the compute')
def step_impl(context):
    deleted = context.compute.delete(skip_destroy=True)
    assert deleted

@behave.then(u'the compute is deleted')
def step_impl(context):
    try:
        context.compute = context.dl.computes.get(context.compute_id)
        assert False, f"TEST FAILED: Expected not found error actual {context.compute}"
    except Exception as err:
        assert 'not found' in str(err).lower(), f"TEST FAILED: Expected not found error actual {err}"