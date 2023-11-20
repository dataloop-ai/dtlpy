import behave


@behave.when(u'I update dataset name to "{new_dataset_name}"')
def step_impl(context, new_dataset_name):
    context.dataset.name = new_dataset_name
    context.project.datasets.update(dataset=context.dataset,
                                  system_metadata=True)


@behave.then(u'I create a dataset by the name of "{new_dataset_name}" in host')
def step_impl(context, new_dataset_name):
    context.dataset_get = context.project.datasets.get(dataset_name=new_dataset_name)
    assert context.dataset_get.name == new_dataset_name


@behave.then(u'There is no dataset by the name of "{original_dataset_name}" in host')
def step_impl(context, original_dataset_name):
    try:
        context.project.datasets.get(dataset_name=original_dataset_name)
        context.error = None
    except Exception as e:
        context.error = e
    assert context.error is not None


@behave.then(u'The dataset from host by the name of "New_Dataset_Name" is equal to the one created')
def step_impl(context):
    dataset_json = context.dataset.to_json()
    dataset_get_json = context.dataset_get.to_json()
    dataset_json.pop('updatedAt', None)
    dataset_get_json.pop('updatedAt', None)
    assert dataset_json == dataset_get_json


@behave.when(u'I try to update the "Original_Dataset_Name" name to a blank name')
def step_impl(context):
    context.dataset.name = ''
    try:
        context.project.datasets.update(dataset=context.dataset, system_metadata=True)
        context.error = None
    except Exception as e:
        context.error = e
    assert context.error is not None


@behave.when(u'I try to update the "Dataset" name to "{existing_dataset_name}"')
def step_impl(context, existing_dataset_name):
    context.dataset.name = existing_dataset_name
    try:
        context.project.datasets.update(dataset=context.dataset, system_metadata=True)
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u'I create a dataset by the name of "{original_dataset_name}"')
def step_impl(context, original_dataset_name):
    context.dataset = context.project.datasets.create(dataset_name=original_dataset_name, index_driver=context.index_driver_var)
