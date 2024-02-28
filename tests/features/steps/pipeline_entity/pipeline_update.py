from behave import when, then, given


@when(u'I update pipeline description')
def step_impl(context):
    context.pipeline.pause()
    context.pipeline = context.project.pipelines.get(pipeline_name=context.pipeline.name)
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
        context.pipeline = context.pipeline.install()
    except Exception as e:
        raise e


@when(u'I update ml node "{node_name}" to variable "{variable_name}"')
def step_impl(context, node_name, variable_name):
    for node in context.pipeline.nodes:
        if node_name == node.name:
            node.metadata['variableModel'] = variable_name
            context.pipeline.update()


@when(u'I update node name to "{node_name}"')
def step_impl(context, node_name):
    context.node = context.pipeline.nodes[0]
    context.node.name = node_name
    context.pipeline.update()


@then(u'I validate task name changed')
def step_impl(context):
    try:
        pipeline_task_name = "{} ({})".format(context.node.name, context.pipeline.name)
        context.task = context.project.tasks.get(task_name=pipeline_task_name)
    except Exception as e:
        assert False, "Failed to get task with the name: {}\n{}".format(pipeline_task_name, e)
