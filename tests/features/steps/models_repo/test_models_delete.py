import behave


@behave.Given(u'There are no models in project')
def step_impl(context):
    models = context.project.models.list()
    count = 0
    for model in models.all():
        model.delete()
        count += 1
    print(f'deleted {count} models')
    if not hasattr(context, 'model_count'):
        context.model_count = 0
