"""
Prompt Item metadata test steps
"""
import json
from behave import given, when, then

@given('I set prompt item metadata to {metadata}')
@when('I set prompt item metadata to {metadata}')
@then('I set prompt item metadata to {metadata}')
def step_impl(context, metadata):
    metadata_dict = json.loads(metadata)
    for key, value in metadata_dict.items():
        context.prompt_item.item.metadata[key] = value
    context.prompt_item.update()

@given('I update the prompt item')
def step_impl(context):
    context.prompt_item.update()

@when('I get the prompt item metadata')
def step_impl(context):
    context.prompt_item.fetch()

@when('I delete the prompt item')
def step_impl(context):
    context.prompt_item = None

@when('I add metadata key "{key}" with value "{value}"')
def step_impl(context, key, value):
    context.prompt_item.metadata[key]=value
    context.prompt_item.item.update(system_metadata=True)

@when('I delete metadata key "{key}"')
def step_impl(context, key):
    del context.prompt_item.metadata[key]
    context.prompt_item.item.update(system_metadata=True)

@when('I update metadata key "{key}" with value "{value}"')
def step_impl(context, key, value):
    context.prompt_item.metadata[key]=value
    context.prompt_item.item.update(system_metadata=True)

@when('I try to update metadata key "{key}" with value "{value}"')
def step_impl(context, key, value):
    try:
        context.prompt_item.metadata[key]=value
        context.prompt_item.item.update(system_metadata=True)
    except KeyError as e:
        context.error = str(e)

@then('The prompt item metadata equals {expected_metadata}')
def step_impl(context, expected_metadata):
    context.prompt_item.fetch()
    # Load the expected metadata from the JSON string
    expected_data = json.loads(expected_metadata)
    actual_data = context.prompt_item.item.metadata

    # Check if all items in expected_data are in actual_data
    for key, expected_value in expected_data.items():
        assert key in actual_data, f"Expected key '{key}' not found in actual metadata: {actual_data}"
        assert actual_data[key] == expected_value, \
            f"Metadata mismatch for key '{key}': Expected '{expected_value}', got '{actual_data[key]}'"

@then('The prompt item {name} does not exist in the dataset')
def step_impl(context, name):
    filters = context.dl.Filters()
    filters.add(field='name', values=name)
    items = context.dataset.items.list(filters=filters)
    assert len(items) == 0, f"Expected no items with name {name}, found {len(items)}"

@then('I get a KeyError with message "{message}"')
def step_impl(context, message):
    expected_error_message = f'"{message}"'
    assert context.error == expected_error_message, f"Expected error message '{expected_error_message}', got '{context.error}'"


@when('I update the prompt item metadata')
def step_impl(context):
    context.prompt_item.metadata["key1"] = "updated_value1"
    context.prompt_item.item = context.dataset.items.upload(local_path=context.prompt_item.to_bytes_io())

@then('The prompt item has the correct metadata')
def step_impl(context):
    context.prompt_item.fetch()
    assert context.prompt_item.metadata["key1"] == "value1", "Metadata key1 is not correct"
    assert context.prompt_item.metadata["key2"] == "value2", "Metadata key2 is not correct"

@then('The prompt item has the updated metadata')
def step_impl(context):
    context.prompt_item.fetch()
    assert context.prompt_item.metadata["key1"] == "updated_value1", "Metadata key1 was not updated"
    assert context.prompt_item.metadata["key2"] == "value2", "Metadata key2 was changed"