from behave import when, then, given


@when(u'I update pipeline description')
def step_impl(context):
    context.pipeline.pause()
    context.pipeline.description = "up"
    context.update_pipeline = context.pipeline.update()


@then(u'Pipeline received equals Pipeline changed except for "description"')
def step_impl(context):
    assert context.pipeline.description == "up"


@then(u'I pause pipeline in context')
@when(u'I pause pipeline in context')
def step_impl(context):
    context.pipeline.pause()


@then(u'I install pipeline in context')
@when(u'I install pipeline in context')
@given(u'I install pipeline in context')
def step_impl(context):
    try:
        context.pipeline.install()
    except Exception as e:
        raise e


