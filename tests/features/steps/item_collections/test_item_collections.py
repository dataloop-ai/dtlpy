import os
import behave
import dtlpy as dl
from dtlpy import exceptions

@behave.when(u'I create a collection with the name "{collection_name}"')
def step_impl(context, collection_name):
    try:
        context.collection = context.dataset.collections.create(name=collection_name)
        assert context.collection.name == collection_name
    except exceptions.PlatformException as e:
        context.error_message = f"Failed to create collection: {str(e)}"
        context.success = False
        raise

@behave.then(u'The collection "{collection_name}" is created successfully')
def step_impl(context, collection_name):
    collections = context.dataset.collections.list_all_collections()
    assert any(c["name"] == collection_name for c in collections), f"Collection '{collection_name}' not found!"

@behave.given(u'I have an existing collection named "{collection_name}"')
def step_impl(context, collection_name):
    try:
        context.collection = context.dataset.collections.create(name=collection_name)
    except exceptions.PlatformException as e:
        if "already exists" in str(e):
            collections = context.dataset.collections.list_all_collections()
            context.collection = next((c for c in collections if c.name == collection_name), None)
            assert context.collection is not None, f"Collection '{collection_name}' could not be retrieved."

@behave.when(u'I try to create a collection with the name "{collection_name}"')
def step_impl(context, collection_name):
    try:
        context.dataset.collections.create(name=collection_name)
        context.success = True
    except ValueError as e:
        context.error_message = str(e)
        context.success = False
    except exceptions.PlatformException as e:
        context.error_message = str(e)
        context.success = False

@behave.then(u'I receive an error stating that the collection name already exists')
def step_impl(context):
    assert not context.success
    assert "already exists" in context.error_message

@behave.when(u'I update the collection name to "{new_name}"')
def step_impl(context, new_name):
    context.updated_collection = context.dataset.collections.update(
        collection_name=context.collection.name,
        new_name=new_name
    )
    assert context.updated_collection.name == new_name

@behave.then(u'The collection name is updated to "{new_name}"')
def step_impl(context, new_name):
    collections = context.dataset.collections.list_all_collections()
    assert any(c['name'] == new_name for c in collections), f"Collection '{new_name}' not found!"

@behave.when(u'I delete the collection "{collection_name}"')
def step_impl(context, collection_name):
    context.dataset.collections.delete(collection_name=collection_name)

@behave.then(u'The collection "{collection_name}" is deleted successfully')
def step_impl(context, collection_name):
    collections = context.dataset.collections.list_all_collections()
    assert not any(c['name'] == collection_name for c in collections), f"Collection '{collection_name}' still exists!"

@behave.when(u'I clone the collection "{collection_name}"')
def step_impl(context, collection_name):
    context.cloned_collection = context.dataset.collections.clone(collection_name=collection_name)

@behave.then(u'A new collection with the name "{expected_name}" is created')
def step_impl(context, expected_name):
    assert context.cloned_collection.name == expected_name

@behave.when(u'I list all collections')
def step_impl(context):
    context.collections = context.dataset.collections.list_all_collections()

@behave.then(u'I receive a list of all collections with their names and keys')
def step_impl(context):
    assert isinstance(context.collections, list), "Expected a list of collections!"
    assert all("key" in c and "name" in c for c in context.collections), "Each collection must have 'key' and 'name' keys!"

@behave.given(u'I have an item in the dataset')
def step_impl(context):
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], "label1.png")
    context.item = context.dataset.items.upload(local_path=local_path)

@behave.when(u'I assign the item to the collection "{collection_name}"')
def step_impl(context, collection_name):
    collections = context.dataset.collections.list_all_collections()
    if not any(c["name"] == collection_name for c in collections):
        context.dataset.collections.create(name=collection_name)
    context.item.assign_collection(collections=[collection_name])

@behave.then(u'The item is assigned to the collection "{collection_name}"')
def step_impl(context, collection_name):
    context.item = context.dataset.items.get(item_id=context.item.id)
    item_collections = context.item.list_collections()
    print(f"Item collections: {item_collections}")  # Debug output for troubleshooting
    assert any(c["name"] == collection_name for c in item_collections), (
        f"Item is not assigned to collection '{collection_name}'!"
    )

@behave.when(u'I unassign the item from the collection "{collection_name}"')
def step_impl(context, collection_name):
    context.item.unassign_collection(collections=[collection_name])

@behave.then(u'The item is no longer assigned to the collection "{collection_name}"')
def step_impl(context, collection_name):
    item_collections = context.item.list_collections()
    assert collection_name not in item_collections

@behave.when(u'I list unassigned items')
def step_impl(context):
    context.unassigned_items = context.dataset.collections.list_all_collections_unassigned_items()

@behave.then(u'I receive a list of item IDs that are not part of any collection')
def step_impl(context):
    assert isinstance(context.unassigned_items, list)
    for item in context.unassigned_items:
        assert not item.list_collections()

@behave.given(u'I have multiple collections in the dataset')
def step_impl(context):
    collection_names = ["Justice League", "Avengers", "X-Men"]
    context.collections = []
    for name in collection_names:
        try:
            collection = context.dataset.collections.create(name=name)
            context.collections.append(collection)
        except exceptions.PlatformException as e:
            if "already exists" in str(e):
                collections = context.dataset.collections.list_all_collections()
                collection = next((c for c in collections if c.name == name), None)
                if collection:
                    context.collections.append(collection)
    assert len(context.collections) == len(collection_names)

@behave.when(u'I list all unassigned items')
def step_impl(context):
    context.unassigned_items = context.dataset.collections.list_unassigned_items()

@behave.then(u'The unassigned items list is accurate')
def step_impl(context):
    assigned_item_ids = {
        item.id
        for collection in context.dataset.collections.list_all_collections()
        for item in collection.items
    }
    unassigned_item_ids = {item.id for item in context.unassigned_items}
    all_item_ids = {item.id for item in context.dataset.items.list()}

    assert assigned_item_ids.isdisjoint(unassigned_item_ids)
    assert assigned_item_ids.union(unassigned_item_ids) == all_item_ids