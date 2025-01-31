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
    context.dataset = context.project.datasets.create(dataset_name=original_dataset_name,
                                                      index_driver=context.index_driver_var)


@behave.when(u'I update dataset metadata "{updated_metadata}"')
def step_impl(context, updated_metadata):
    metadata_parts = updated_metadata.split(".")
    metadata_category = metadata_parts[0]
    metadata_key, metadata_value = metadata_parts[1].split(":")
    metadata_value = metadata_value.strip("'")
    if metadata_category not in context.dataset.metadata:
        context.dataset.metadata[metadata_category] = {}
    context.dataset.metadata[metadata_category][metadata_key] = metadata_value
    is_system_metadata = metadata_category == "system"
    context.dataset.update(system_metadata=is_system_metadata)


@behave.then(u'I validate for "{entity}" that the updated metadata is "{updated_metadata}"')
def step_impl(context, entity, updated_metadata):
    field, expected_value = updated_metadata.split(':')
    field_path = field.split('.')
    if entity == "dataset":
        dataset = context.dataset_list[0]
        actual_value = dataset.metadata
    elif entity == "item":
        item = context.dataset.items.get(None, context.item.id)
        actual_value = item.metadata
    else:
        raise AssertionError(f"Unknown object: {entity}")
    for key in field_path:
        actual_value = actual_value.get(key)
        if actual_value is None:
            raise AssertionError(f"Field '{field}' not found in metadata")
    if isinstance(actual_value, (int, float)):
        expected_value = type(actual_value)(expected_value)
    elif isinstance(actual_value, bool):
        expected_value = expected_value.lower() == 'true'
    assert actual_value == expected_value, f"Expected {field} to be {expected_value} but got {actual_value}"

@behave.when(u'I update cloned dataset name to "{new_dataset_name}"')
def step_impl(context, new_dataset_name):
    context.clone_dataset.name = new_dataset_name
    context.project.datasets.update(dataset=context.clone_dataset,
                                    system_metadata=True)