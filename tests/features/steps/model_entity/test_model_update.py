import behave


@behave.when(u'I change model tags')
def step_impl(context):
    context.new_model_tags = context.model.tags + ['newTage1', 'newTag2']
    context.model.tags = context.new_model_tags
    context.model.update()


@behave.then(u'Model tags was changed')
def step_impl(context):
    new_model = context.dl.models.get(model_id=context.model.id)
    new_tags = new_model.tags.sort()
    should_be_tags = context.new_model_tags.sort()
    assert new_tags == should_be_tags, "tags didn't change! New: {!r}, Should be: {!r}".format(
        new_tags,
        should_be_tags
    )
