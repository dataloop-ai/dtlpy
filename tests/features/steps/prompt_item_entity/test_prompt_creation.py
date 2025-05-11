"""
Prompt Item creation test steps
"""
from behave import then
from dtlpy.entities.prompt_item import PromptType

@then('The prompt item contains text prompt "{text}"')
def step_impl(context, text):
    context.prompt_item.fetch()
    found = False
    for prompt in context.prompt_item.prompts:
        for element in prompt.elements:
            if element['mimetype'] == PromptType.TEXT and element['value'] == text:
                found = True
                break
        if found:
            break
    assert found, f"Text prompt '{text}' not found in prompt item"

@then('The prompt item contains image prompt')
def step_impl(context):
    context.prompt_item.fetch()
    found = False
    for prompt in context.prompt_item.prompts:
        for element in prompt.elements:
            if element['mimetype'] == PromptType.IMAGE:
                found = True
                break
        if found:
            break
    assert found, "Image prompt not found in prompt item"

@then('The prompt item contains "{count}" prompts')
def step_impl(context, count):
    context.prompt_item.fetch()
    assert len(context.prompt_item.prompts) == int(count), \
        f"Expected {count} prompts, found {len(context.prompt_item.prompts)}" 