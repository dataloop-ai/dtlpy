import behave
from dtlpy import entities


@behave.when(u'I change entity to "{entity}"')
def step_impl(context, entity):
    if entity == "Item":
        entity = entities.Item
    elif entity == "Artifact":
        entity = entities.Artifact
    elif entity == "Package":
        entity = entities.Package

    context.dataset.items.set_items_entity(entity)


@behave.then(u'Items item entity is "{entity}"')
def step_impl(context, entity):
    if entity == "Item":
        entity = entities.Item
    elif entity == "Artifact":
        entity = entities.Artifact
    elif entity == "Package":
        entity = entities.Package

    assert context.dataset.items.items_entity == entity


@behave.when(u'I try to change entity to "Dataset"')
def step_impl(context):
    try:
        context.dataset.items.set_items_entity(entities.Dataset)
        context.error = None
    except Exception as e:
        context.error = e
