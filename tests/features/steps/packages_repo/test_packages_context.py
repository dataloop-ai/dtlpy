import behave


@behave.given(u'I set Project to Project {project_index}')
def step_impl(context, project_index):
    context.project = context.projects[int(project_index) - 1]


@behave.when(u'I get the package from project number {project_index}')
def step_impl(context, project_index):
    context.package = context.projects[int(project_index) - 1].packages.get(package_id=context.package.id)


@behave.then(u'package Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.package.project_id == context.projects[int(project_index)-1].id


@behave.then(u'package Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.package.project.id == context.projects[int(project_index)-1].id
