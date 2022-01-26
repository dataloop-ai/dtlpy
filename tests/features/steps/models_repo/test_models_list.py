import behave


@behave.given(u'I create "{num_models}" models')
def step_impl(context, num_models):
    models = list()
    for i_model in range(int(num_models)):
        models.append(context.project.models.create(model_name='model-num-{}'.format(i_model)))
    context.models = models


@behave.when(u'I list model with filter field "{field}" and values "{values}"')
def step_impl(context, field, values):
    filters = context.dl.Filters(resource='models',
                                 field=field,
                                 values=values)
    context.list_results = context.project.models.list(filters=filters)


@behave.then(u'I get "{num}" entities')
def step_impl(context, num):
    assert len(context.list_results) == int(num), \
        'Got wrong number of entities. expected: {!r}, found {!r}'.format(num, context.list_results.items_count)
