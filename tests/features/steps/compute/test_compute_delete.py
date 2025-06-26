import behave


@behave.then(u'I able to delete compute')
def step_impl(context):
    context.compute.delete(skip_destroy=True)
    context.to_delete_computes_ids.remove(context.compute_id)
