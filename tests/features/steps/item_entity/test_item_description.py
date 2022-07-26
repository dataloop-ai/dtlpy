import behave


@behave.when(u'I Add description "{text}" to item')
def step_impl(context, text):
    context.item = context.item.set_description(text)


@behave.then(u'I validate item.description annotation')
def step_impl(context):
    filters = context.dl.Filters(field='type', values='item_description', resource=context.dl.FiltersResource.ANNOTATION)

    annotation = context.item.annotations.list(filters=filters)
    assert annotation.annotations, "TEST FAILED: No annotation found"
    assert annotation.annotations[0].metadata['system']['system'], "TEST FAILED: Annotation has no system system true\n{}".format(annotation.to_json())
    assert annotation.annotations[0].metadata['system']['automated'], "TEST FAILED: Annotation has no system system true\n{}".format(annotation.to_json())

