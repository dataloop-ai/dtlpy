import behave


@behave.when(u'I create "{num_models}" models')
def step_impl(context, num_models):
    models = list()
    for i_model in range(int(num_models)):
        models.append(context.package.models.create(model_name='model-num-{}'.format(i_model),
                                                    dataset_id=context.dataset.id,
                                                    labels=[]))
    context.models = models


@behave.when(u'I list models with filter field "{field}" and values "{values}"')
def step_impl(context, field, values):
    filters = context.dl.Filters(resource='models',
                                 field=field,
                                 values=values)
    context.list_results = list(context.package.models.list(filters=filters).all())


@behave.then(u'I get "{models_number}" entities')
def step_impl(context, models_number):
    assert len(context.list_results) == int(models_number)
