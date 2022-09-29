import behave


@behave.when(u'There are no models')
def step_impl(context):
    models = context.package.models.list()
    count = 0
    for model in models.all():
        model.delete()
        count += 1
    print('deleted {} models from package {}'.format(count, context.package.name))
    if not hasattr(context, 'model_count'):
        context.model_count = 0
