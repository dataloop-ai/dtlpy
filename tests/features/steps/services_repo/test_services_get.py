import behave


@behave.when(u'I get service by id')
def step_impl(context):
    context.service_get = context.project.services.get(service_id=context.service.id)


@behave.when(u'I get service by name')
def step_impl(context):
    context.service_get = context.project.services.get(service_name=context.service.name)


@behave.then(u'Service received equals to service created')
def step_impl(context):
    assert context.service.to_json() == context.service_get.to_json()


@behave.then(u'I expect preemptible value to be "{value}"')
def step_impl(context, value):
    assert context.service.runtime.preemptible == eval(value), "TEST FAILED: Expected preemptible to be {} , Got {}".format(value, context.service.execution_timeout)


@behave.when(u'I get service in index "{service_index}"')
def step_impl(context, service_index):
    context.service = context.project.services.list()[0][int(service_index)]
