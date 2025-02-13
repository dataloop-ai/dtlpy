import behave


@behave.when(u'I try to create the compute from context.original_path')
def step_impl(context):
    try:
        org_id = context.project.org['id']
        context.compute = context.dl.computes.create_from_config_file(context.original_path, org_id)
        context.compute_id = context.compute.id
        context.to_delete_computes_ids.append(context.compute_id)
        context.error = None
    except Exception as e:
        context.error = e
