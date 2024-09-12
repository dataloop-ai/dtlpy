import behave


@behave.when(u'I rename model to "{model_name}"')
def step_impl(context, model_name):
    context.model.name = model_name
    context.model.update()


@behave.then(u'model name is "{model_name}"')
def step_impl(context, model_name):
    context.model = context.dl.models.get(model_id=context.model.id)
    assert context.model.name == model_name, f"TEST FAILED: model name is different. from be: {context.model.name}, from context: {model_name}"


@behave.then(u'The model name not changed')
def step_impl(context):
    model_name = context.model.name
    model = context.project.models.get(model_id=context.model.id)
    assert model_name == model.name, f"TEST FAILED: Expected model name: '{model_name}', Actual: '{model.name}'"