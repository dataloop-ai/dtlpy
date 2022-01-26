import behave


@behave.given(u'I create "{num_snapshots}" snapshots')
def step_impl(context, num_snapshots):
    snapshots = list()
    for model in context.models:
        for i_model in range(int(num_snapshots)):
            snapshots.append(model.snapshots.create(snapshot_name='snapshot-num-{}'.format(i_model),
                                                    dataset_id=context.dataset.id,
                                                    labels=[]))
    context.snapshots = snapshots


@behave.when(u'I list snapshots with filter field "{field}" and values "{values}"')
def step_impl(context, field, values):
    filters = context.dl.Filters(resource='snapshots',
                                 field=field,
                                 values=values)
    context.list_results = []
    for model in context.models:
        context.list_results += list(model.snapshots.list(filters=filters).all())
