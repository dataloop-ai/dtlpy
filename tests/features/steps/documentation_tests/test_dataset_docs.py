import behave
import random


@behave.given(u'Create a Dataset "{dataset_name}"')
def step_impl(context, dataset_name):
    dataset_name = dataset_name + str(random.randint(10000, 100000))
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)


@behave.when(u'Create a Dataset "{dataset_name}"')
def step_impl(context, dataset_name):
    dataset_name = dataset_name + str(random.randint(10000, 100000))
    context.dataset = context.project.datasets.create(dataset_name=dataset_name, index_driver=context.index_driver_var)


@behave.when(u'Get Commands - Get Projects Datasets List')
def step_impl(context):
    context.datasets = context.project.datasets.list()


@behave.then(u'Get Dataset by Name')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_name=context.dataset.name)


@behave.then(u'Get a dataset by ID')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_id=context.dataset.id)


@behave.then(u'Print a Dataset')
def step_impl(context):
    context.dataset.print()


@behave.then(u'I try to get a dataset by the name of "{dataset_name}"')
def step_impl(context, dataset_name):
    try:
        context.dataset = context.project.datasets.get(dataset_name=dataset_name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'Clone Dataset "{clone_dataset_name}"')
def step_impl(context, clone_dataset_name):
    context.clone_dataset = context.dataset.clone(clone_name=clone_dataset_name, filters=None,
                                                  with_items_annotations=True, with_metadata=True,
                                                  with_task_annotations_status=True)


@behave.when(u'I clone an item')
def step_impl(context):
    context.cloned_item = context.item.clone(with_annotations=True, with_metadata=True,
                                             with_task_annotations_status=False, allow_many=True)


@behave.then(u'I validate image pre run on cloned item')
def step_impl(context):
    executions = context.cloned_item.resource_executions.list()
    image_pre_run = False
    for page in executions:
        for execution in page:
            if execution.package_name == 'image-preprocess':
                image_pre_run = True
    assert image_pre_run is True, 'image-preprocess package did not run on cloned item'


@behave.then(u'Merge Datasets "{merge_dataset_name}"')
def step_impl(context, merge_dataset_name):
    context.dataset_ids = [context.dataset.id, context.clone_dataset.id]
    context.project_ids = [context.dataset.project.id, context.clone_dataset.project.id]
    context.datasetMerge = context.dl.datasets.merge(merge_name=merge_dataset_name, project_ids=context.project_ids,
                                                     dataset_ids=context.dataset_ids, with_items_annotations=True,
                                                     with_metadata=False,
                                                     with_task_annotations_status=False)

    project__datasets_list = context.project.datasets.list()

    assert len(project__datasets_list) == 4
