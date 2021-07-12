from behave import given, when, then


@when(u'I delete a pipeline by the name of "{pipeline_delete}"')
def step_impl(context, pipeline_delete):
    context.project.pipelines.delete(pipeline_name=pipeline_delete)


@when(u'I delete a pipeline by the id')
def step_impl(context):
    context.project.pipelines.delete(pipeline_id=context.pipeline.id)


@then(u'There are no pipeline by the name of "{pipeline_delete}"')
def step_impl(context, pipeline_delete):
    try:
        pipeline = None
        pipeline = context.dl.pipelines.get(pipeline_name=pipeline_delete)
    except context.dl.exceptions.NotFound:
        assert pipeline is None


@when(u'I try to delete a pipeline by the name of "{pipeline_name}"')
def step_impl(context, pipeline_name):
    try:
        context.project.pipelines.delete(pipeline_name=pipeline_name,)
        context.error = None
    except Exception as e:
        context.error = e
