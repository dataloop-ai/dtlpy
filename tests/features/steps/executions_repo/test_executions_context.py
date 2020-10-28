import behave


@behave.given(u'I append service to services')
def step_impl(context):
    if not hasattr(context, "services"):
        context.services = list()
    context.services.append(context.service)


@behave.when(u'I get the execution from project number {project_index}')
def step_impl(context, project_index):
    context.execution = context.projects[int(project_index) - 1].executions.get(execution_id=context.execution.id)


@behave.when(u'I get the execution from service number {project_index}')
def step_impl(context, project_index):
    context.execution = context.services[int(project_index) - 1].executions.get(execution_id=context.execution.id)


@behave.then(u'Execution Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.execution.project_id == context.projects[int(project_index)-1].id


@behave.then(u'Execution Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.execution.project.id == context.projects[int(project_index)-1].id


@behave.then(u'Execution Service_id is equal to service {service_index} id')
def step_impl(context, service_index):
    assert context.execution.service_id == context.services[int(service_index) - 1].id


@behave.then(u'Execution Service.id is equal to service {service_index} id')
def step_impl(context, service_index):
    assert context.execution.service.id == context.services[int(service_index) - 1].id
