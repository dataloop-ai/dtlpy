import behave


@behave.when(u"I get execution by id")
def step_impl(context):
    context.execution_get = context.service.executions.get(execution_id=context.execution.id)


@behave.then(u"I receive an Execution object")
def step_impl(context):
    assert isinstance(context.execution_get, context.dl.entities.Execution)


@behave.then(u"Execution received equals to execution created")
def step_impl(context):
    assert context.execution_get.to_json() == context.execution.to_json()
