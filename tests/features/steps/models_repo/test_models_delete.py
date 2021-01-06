import behave


@behave.when(u'I delete the model that was created by name')
def step_impl(context):
    context.project.models.delete(model_name=context.model.name)


@behave.when(u'I delete the model that was created by id')
def step_impl(context):
    context.project.models.delete(model_id=context.model.id)


@behave.when(u'I try to delete a model by the name of "{model_name}"')
def step_impl(context, model_name):
    try:
        context.project.models.delete(model_name=model_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No model was deleted')
def step_impl(context):
    assert len(context.project.models.list()) == context.model_count
