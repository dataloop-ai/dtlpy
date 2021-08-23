from behave import when, then


@when(u'I update pipeline description')
def step_impl(context):
    context.pipeline.description = "up"
    context.update_pipeline = context.pipeline.update()


@then(u'Pipeline received equals Pipeline changed except for "description"')
def step_impl(context):
    assert context.pipeline.description == "up"
