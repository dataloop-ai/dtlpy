import behave


@behave.when(u'I get an Assignment')
def step_impl(context):
    context.assignment = context.task.assignments.list()[0]


@behave.given(u'I set Dataset to Dataset {dataset_index}')
def step_impl(context, dataset_index):
    context.dataset = context.datasets[int(dataset_index) - 1]


@behave.when(u'I append task to tasks')
def step_impl(context):
    if not hasattr(context, "tasks"):
        context.tasks = list()
    context.tasks.append(context.task)


@behave.when(u'I get the assignment from project number {project_index}')
def step_impl(context, project_index):
    context.assignment = context.projects[int(project_index) - 1].assignments.get(assignment_id=context.assignment.id)


@behave.when(u'I get the assignment from dataset number {dataset_index}')
def step_impl(context, dataset_index):
    context.assignment = context.datasets[int(dataset_index) - 1].assignments.get(assignment_id=context.assignment.id)


@behave.then(u'assignment Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.assignment.project_id == context.projects[int(project_index)-1].id


@behave.then(u'assignment Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.assignment.project.id == context.projects[int(project_index)-1].id


@behave.then(u'assignment Dataset_id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.assignment.dataset_id == context.datasets[int(dataset_index)-1].id


@behave.then(u'assignment Dataset.id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.assignment.dataset.id == context.datasets[int(dataset_index)-1].id


@behave.then(u'assignment Task_id is equal to task {task_index} id')
def step_impl(context, task_index):
    assert context.assignment.task_id == context.tasks[int(task_index)-1].id


@behave.then(u'assignment Task.id is equal to task {task_index} id')
def step_impl(context, task_index):
    assert context.assignment.task.id == context.tasks[int(task_index)-1].id
