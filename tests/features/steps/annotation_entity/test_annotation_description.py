import behave


@behave.when(u'I add description "{text}" to the annotation')
def step_impl(context, text):
    context.annotation.description = text
    context.annotation.update()


@behave.then(u'I validate annotation.description has "{text}" value')
def step_impl(context, text):
    if text == "None":
        text = None

    context.annotation = context.item.annotations.get(annotation_id=context.annotation.id)
    assert context.annotation.description == text


@behave.when(u'I remove description from the annotation')
def step_impl(context):
    context.annotation.description = None
    context.annotation.update()
