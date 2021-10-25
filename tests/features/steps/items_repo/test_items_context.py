import behave


@behave.when(u'I get the item from project number {project_index}')
def step_impl(context, project_index):
    context.item = context.projects[int(project_index) - 1].items.get(item_id=context.item.id)


@behave.when(u'I get the item from dataset number {dataset_index}')
def step_impl(context, dataset_index):
    context.item = context.datasets[int(dataset_index) - 1].items.get(item_id=context.item.id)


@behave.then(u'item Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.item.projectId == context.projects[int(project_index)-1].id


@behave.then(u'item Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.item.project.id == context.projects[int(project_index)-1].id


@behave.then(u'item Dataset_id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.item.dataset_id == context.datasets[int(dataset_index)-1].id


@behave.then(u'item Dataset.id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.item.dataset.id == context.datasets[int(dataset_index)-1].id
