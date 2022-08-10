import behave


@behave.when(u'I Add description "{text}" to item')
def step_impl(context, text):
    context.item = context.item.set_description(text)


@behave.then(u'I validate item.description has "{text}" value')
def step_impl(context, text):
    assert context.item.description == text

