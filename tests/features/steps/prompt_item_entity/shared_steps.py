"""
Shared steps for prompt item tests
"""
from behave import given, when, then
import os
import json
import io
from dtlpy.entities.prompt_item import PromptItem, Prompt, PromptType
from dtlpy.entities.item import Item

@given(u"There is a JSON item")
def step_impl(context):
    # Check which feature is running
    feature_filename = os.path.basename(context.feature.filename)

    # For metadata tests, upload a minimal valid JSON item
    print(f"Feature {feature_filename}: Uploading minimal JSON item.")
    name = "metadata_test_item.json" # Give it a distinct name
    minimal_prompt_json = {
        "shebang": "dataloop",
        "metadata": {"dltype": "prompt"}, # Initial metadata can be empty or minimal
        "prompts": {}
    }
    byte_io = io.BytesIO()
    byte_io.name = name
    byte_io.write(json.dumps(minimal_prompt_json).encode())
    byte_io.seek(0)
    context.item = context.dataset.items.upload(local_path=byte_io, overwrite=True)
    print(f"Uploaded JSON item: {context.item.id}, Name: {context.item.name}")

    assert isinstance(context.item, Item), "Background step failed to create a dl.Item object in context.item"

@given('I create a prompt item with name "{name}"')
def step_impl(context, name):
    # This step now expects context.item to be correctly set by the background
    if not hasattr(context, 'item') or not isinstance(context.item, Item):
        raise ValueError("Background step did not provide a valid context.item")

    # Instantiate PromptItem using the item from the background step
    context.prompt_item = PromptItem(name=name, item=context.item)
    print(f"Instantiated PromptItem '{name}' using item {context.item.id}")
    # No immediate upload here, subsequent steps handle prompts/metadata/upload

@given('I create a prompt with key "{key}"')
def step_impl(context, key):
    context.current_prompt = Prompt(key=key)

@given('I add text element to prompt with value "{value}"')
def step_impl(context, value):
    context.current_prompt.add_element(value=value, mimetype=PromptType.TEXT)

@given('I add image element to prompt with value "{value}"')
def step_impl(context, value):
    context.current_prompt.add_element(value=value, mimetype=PromptType.IMAGE)

@given('I add the prompt to the prompt item')
def step_impl(context):
    context.prompt_item.prompts.append(context.current_prompt)

@when('I update the prompt item')
def step_impl(context):
    context.prompt_item.update()

@then('The prompt item exists in the dataset')
def step_impl(context):
    items = context.dataset.items.list(filters={'name': context.prompt_item.name})
    assert len(items) == 1, f"Expected 1 item with name {context.prompt_item.name}, found {len(items)}" 