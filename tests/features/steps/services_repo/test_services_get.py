import behave
import time


@behave.when(u'I get service by id')
def step_impl(context):
    context.service_get = context.project.services.get(service_id=context.service.id)


@behave.when(u'I set service in context')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.service.id)


@behave.then(u'Service is archived')
def step_impl(context):
    for x in range(5):
        context.service_get = context.project.services.get(service_id=context.service_get.id)
        if context.service_get.archive:
            break
        time.sleep(1)
    assert context.service_get.archive is True, "TEST FAILED: Expected archived to be True , Got {}".format(
        context.service_get.archive)


@behave.when(u'I get service by name')
def step_impl(context):
    context.service_get = context.project.services.get(service_name=context.service.name)


@behave.given(u'I get service by name "{input_name}"')
@behave.when(u'I get service by name "{input_name}"')
def step_impl(context, input_name):
    context.service = context.project.services.get(service_name=input_name)


@behave.then(u'Service received equals to service created')
def step_impl(context):
    assert context.service.to_json() == context.service_get.to_json()


@behave.then(u'I expect preemptible value to be "{value}"')
def step_impl(context, value):
    assert context.service.runtime.preemptible == eval(
        value), "TEST FAILED: Expected preemptible to be {} , Got {}".format(value, context.service.execution_timeout)


@behave.when(u'I get service in index "{service_index}"')
def step_impl(context, service_index):
    f = context.dl.Filters(resource=context.dl.FiltersResource.SERVICE)
    f.sort_by(field='createdAt')
    context.service = context.project.services.list().items[int(service_index)]


@behave.when(u'I get service from context.execution')
def step_impl(context):
    context.service = context.project.services.get(service_id=context.execution.service_id)


@behave.then(u'Integration display on service secrets')
def step_impl(context):
    if not hasattr(context, "integration"):
        raise AttributeError("Please make sure context has attr 'integration'")

    assert context.integration.id in context.service.secrets, \
        f"TEST FAILED: Expected integration to be in service secrets, Actual: {context.service.secrets}"


@behave.then(u'service status is "{service_status}"')
def step_impl(context, service_status):
    context.service = context.project.services.get(service_id=context.service.id)
    if service_status.lower() == "active":
        active = True
    elif service_status.lower() == "paused":
        active = False
    else:
        raise ValueError(f"Invalid service status please choose between 'active' or 'paused'")

    assert context.service.active == active, \
        f"TEST FAILED: Expected service status active to be {active}, Actual: {context.service.active}"
