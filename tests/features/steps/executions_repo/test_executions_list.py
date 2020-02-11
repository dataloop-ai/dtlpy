import behave


@behave.when(u"I list service executions")
def step_impl(context):
    context.execution_list = context.service.executions.list()


@behave.then(u'I receive a list of "{count}" executions')
def step_impl(context, count):
    assert len(context.execution_list.items) == int(count)
    if int(count) > 0:
        for page in context.execution_list:
            for execution in page:
                assert isinstance(execution, context.dl.entities.Execution)
