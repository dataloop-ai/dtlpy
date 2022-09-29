import behave


@behave.when(u'I rename model to "{model_name}"')
def step_impl(context, model_name):
    context.model.name = model_name
    context.model.update()


@behave.then(u'model name is "{model_name}"')
def step_impl(context, model_name):
    model = context.dl.models.get(model_id=context.model.id)
    assert model.name == model_name, "model name is different. from be: {}, from context: {}".format(model.name,
                                                                                                     model_name)
