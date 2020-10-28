import behave


@behave.when(u'I get the trigger from project number {project_index}')
def step_impl(context, project_index):
    context.trigger = context.projects[int(project_index) - 1].triggers.get(trigger_id=context.trigger.id)


@behave.when(u'I get the trigger from service number {project_index}')
def step_impl(context, project_index):
    context.trigger = context.services[int(project_index) - 1].triggers.get(trigger_id=context.trigger.id)


@behave.then(u'Trigger Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.trigger.project_id == context.projects[int(project_index)-1].id


@behave.then(u'Trigger Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.trigger.project.id == context.projects[int(project_index)-1].id


@behave.then(u'Trigger Service_id is equal to service {service_index} id')
def step_impl(context, service_index):
    assert context.trigger.service_id == context.services[int(service_index) - 1].id


@behave.then(u'Trigger Service.id is equal to service {service_index} id')
def step_impl(context, service_index):
    assert context.trigger.service.id == context.services[int(service_index) - 1].id
