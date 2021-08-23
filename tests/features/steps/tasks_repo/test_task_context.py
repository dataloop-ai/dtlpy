import os

import behave
from .. import fixtures


@behave.given(u'I create task belong to dataset {dataset_index}')
def step_impl(context, dataset_index):
    context.params = {param.split('=')[0]: fixtures.get_value(params=param.split('='), context=context) for param in
                      context.table.headings if
                      fixtures.get_value(params=param.split('='), context=context) is not None}
    context.task = context.datasets[int(dataset_index) - 1].tasks.create(**context.params)


@behave.given(u'I upload items in "{item_path}" to datasets')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    for dataset in context.datasets:
        dataset.items.upload(local_path=item_path)


@behave.when(u'I get the task from project number {project_index}')
def step_impl(context, project_index):
    context.task = context.projects[int(project_index) - 1].tasks.get(task_id=context.task.id)


@behave.when(u'I get the task from dataset number {dataset_index}')
def step_impl(context, dataset_index):
    context.task = context.datasets[int(dataset_index) - 1].tasks.get(task_id=context.task.id)


@behave.then(u'task Project_id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.task.project_id == context.projects[int(project_index) - 1].id


@behave.then(u'task Project.id is equal to project {project_index} id')
def step_impl(context, project_index):
    assert context.task.project.id == context.projects[int(project_index) - 1].id


@behave.then(u'task Dataset_id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.task.dataset_id == context.datasets[int(dataset_index) - 1].id


@behave.then(u'task Dataset.id is equal to dataset {dataset_index} id')
def step_impl(context, dataset_index):
    assert context.task.dataset.id == context.datasets[int(dataset_index) - 1].id
