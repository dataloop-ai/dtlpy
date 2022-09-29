import behave


@behave.then(u'I delete package')
def step_impl(context):
    try:
        context.package.delete()
    except Exception as e:
        context.error = e
        assert False, "FAILED TEST: Failed to delete package {} ID : {}".format(context.package.name, context.package.id)
