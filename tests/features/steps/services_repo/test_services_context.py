import behave
import dtlpy as dl


@behave.given(u'I append package to packages')
def step_impl(context):
    if not hasattr(context, "packages"):
        context.packages = list()
    context.packages.append(context.package)


@behave.when(u'I get the service from project number {project_index}')
def step_impl(context, project_index):
    context.service = context.projects[int(project_index) - 1].services.get(service_id=context.service.id)


@behave.when(u'I get the service from package number {project_index}')
def step_impl(context, project_index):
    context.service = context.packages[int(project_index) - 1].services.get(service_id=context.service.id)


@behave.then(u'Service Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.service.project_id == context.projects[int(project_index)-1].id


@behave.then(u'Service Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.service.project.id == context.projects[int(project_index)-1].id


@behave.then(u'Service Package_id is equal to package {project_index} id')
def step_impl(context, project_index):
    assert context.service.package_id == context.packages[int(project_index) - 1].id


@behave.then(u'Service Package.id is equal to package {project_index} id')
def step_impl(context, project_index):
    assert context.service.package.id == context.packages[int(project_index) - 1].id
