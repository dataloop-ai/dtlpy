"""
Prompt Item response test steps
"""
import os
from behave import when, then
import dtlpy as dl
from dtlpy.entities.prompt_item import PromptType
import behave # Ensure behave is imported

@behave.given('I upload an image with name "{filename}"')
def step_impl(context, filename):
    assets_path = os.environ.get('DATALOOP_TEST_ASSETS')
    if not assets_path:
        raise ValueError("Environment variable 'DATALOOP_TEST_ASSETS' is not set.")
    local_path = os.path.join(assets_path, filename)
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Asset file not found: {local_path}")
    print(f"Uploading item from: {local_path}")
    # Upload the image and store the returned item in context.item
    context.item = context.dataset.items.upload(local_path=local_path)
    assert isinstance(context.item, dl.Item), "Failed to upload item or return type is not dl.Item"
    print(f"Uploaded item ID: {context.item.id}, Name: {context.item.name}")

@when('I add text response to prompt with model "{model_name}", key "{key}" and value "{response}"')
def step_impl(context, model_name, key, response):
    context.prompt_item.add(
        prompt_key=key,
        message={
            "role": "assistant",
            "content": [{
                "mimetype": PromptType.TEXT,
                "value": response
            }]
        },
        model_info={"name": model_name, "confidence": 0.95, "model_id": "test_model_id"}
    )

@when('I add image response to prompt with key "{key}" using the uploaded image')
def step_impl(context, key):
    if not hasattr(context, 'item') or context.item is None:
        raise ValueError("Context does not contain a valid 'item' for the image response.")
    context.prompt_item.add(
        prompt_key=key,
        message={
            "role": "assistant",
            "content": [{
                "mimetype": PromptType.IMAGE,
                "value": context.item.id
            }]
        }
    )
    # Revert to using items.upload to save the prompt item with added response
    context.prompt_item.item = context.dataset.items.upload(local_path=context.prompt_item.to_bytes_io(), overwrite=True)

@then('The prompt item contains text response "{response}"')
def step_impl(context, response):
    found = False
    for content in context.prompt_item.assistant_prompts:
        for element in content.elements:
            if element.get('mimetype') == PromptType.TEXT and element.get('value') == response:
                found = True
                break
        if found:
            break
    assert found, f"Text response '{response}' not found in prompt item annotations"

@then('The prompt item contains image response')
def step_impl(context):
    found = False
    for content in context.prompt_item.assistant_prompts:
        for element in content.elements:
            if element.get('mimetype') == PromptType.IMAGE:
                found = True
                break
        if found: break
    assert found, "Image response not found in prompt item annotations"

@then('The response has model info')
def step_impl(context):
    found = False
    for content in context.prompt_item.assistant_prompts:
        system_meta = content.metadata
        model_info = system_meta.get('model_info', system_meta.get('model'))
        if isinstance(model_info, dict) and 'name' in model_info and 'confidence' in model_info:
            found = True
            break
    assert found, "Response with model info (name, confidence) not found in prompt item annotations"

@then('The prompt with key "{key}" contains responses "{response1}" and "{response2}"')
def step_impl(context, key, response1, response2):
    context.prompt_item.fetch()
    item = context.prompt_item._item
    if item is None:
        raise ValueError("PromptItem's underlying item (_item) is None after fetch.")
    all_annotations = item.annotations.list()
    responses_found = []
    for annotation in all_annotations:
        if annotation.label == 'response':
            system_meta = annotation.metadata.get('system', {})
            # Check if the annotation is associated with the correct prompt key
            if system_meta.get('prompt_key') == key:
                message_meta = system_meta.get('message', {})
                content_list = message_meta.get('content', [])
                for content in content_list:
                    if content.get('mimetype') == PromptType.TEXT:
                        responses_found.append(content.get('value'))

    assert response1 in responses_found, f"Response '{response1}' not found in annotations for prompt key '{key}'"
    assert response2 in responses_found, f"Response '{response2}' not found in annotations for prompt key '{key}'" 