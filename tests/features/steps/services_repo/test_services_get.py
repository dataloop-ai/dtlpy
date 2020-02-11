import behave
import os


@behave.when(u'I get service by id')
def step_impl(context):
    context.service_get = context.project.services.get(service_id=context.service.id)


@behave.when(u'I get service by name')
def step_impl(context):
    context.service_get = context.project.services.get(service_name=context.service.name)

@behave.then(u'Service received equals to service created')
def step_impl(context):
    assert context.service.to_json() == context.service_get.to_json()
