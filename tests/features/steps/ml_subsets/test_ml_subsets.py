import behave
import dtlpy as dl
import random


@behave.given(u'I upload 10 items to the dataset')
def step_impl(context):
    # Assuming 'context.dataset' is already created in the background steps
    # Upload 10 dummy items (you can upload real files, or mock this logic)
    for i in range(10):
        context.dataset.items.upload(local_path='/path/to/dummy/file{}.jpg'.format(i))
    # Refresh dataset
    context.items = list(context.dataset.items.list().all())
    assert len(context.items) == 10


@behave.when(u'I split dataset items into ML subsets with default percentages')
def step_impl(context):
    # Using default percentages of 80-10-10
    filters = dl.Filters(field='type', values='file')
    context.dataset.split_ml_subsets(items_query=filters)


@behave.then(u'Items are splitted according to the default ratio')
def step_impl(context):
    # After splitting, ~80% train, ~10% val, ~10% test.
    # Let's count subsets.
    items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    train_count = 0
    val_count = 0
    test_count = 0
    for item in items:
        subset = item.get_current_subset()
        if subset == 'train':
            train_count += 1
        elif subset == 'validation':
            val_count += 1
        elif subset == 'test':
            test_count += 1

    assert train_count > 0
    assert val_count > 0
    assert test_count > 0
    # Simple ratio check (not exact due to rounding):
    # Just ensure distribution is as expected.
    total = len(items)
    assert abs((train_count/total)*100 - 80) < 20  # Tolerant check
    assert abs((val_count/total)*100 - 10) < 10
    assert abs((test_count/total)*100 - 10) < 10


@behave.given(u'I select 3 specific items from the dataset')
def step_impl(context):
    # Just pick first 3 items
    context.items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    context.selected_item_ids = [item.id for item in context.items[:3]]
    

@behave.when(u'I assign the \'train\' subset to those selected items')
def step_impl(context):
    filters = dl.Filters()
    filters.add(field='id', values=context.selected_item_ids, operator=dl.FiltersOperations.IN)
    response = context.dataset.assign_subset_to_items(items_query=filters, subset='train')
    assert response == True

@behave.then(u'Those items have train subset assigned')
def step_impl(context):
    for item_id in context.selected_item_ids:
        item = context.dataset.items.get(item_id=item_id)
        result = item.get_current_subset()
        assert result == 'train'


@behave.when(u'I remove subsets from those selected items')
def step_impl(context):
    filters = dl.Filters()
    filters.add(field='id', values=context.selected_item_ids, operator=dl.FiltersOperations.IN)
    response = context.dataset.remove_subset_from_items(items_query=filters)
    assert response == True


@behave.then(u'Those items have no ML subset assigned')
def step_impl(context):
    for item_id in context.selected_item_ids:
        item = context.dataset.items.get(item_id=item_id)
        result = item.get_current_subset()
        assert result is None


@behave.given(u'I have a single item from the dataset')
def step_impl(context):
    context.items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    # pick one random item
    context.single_item = context.items[0]


@behave.when(u'I assign the \'validation\' subset to this item at the item level')
def step_impl(context):
    context.single_item.assign_subset('validation')


@behave.then(u'The item has \'validation\' subset assigned')
def step_impl(context):
    result = context.single_item.get_current_subset()
    assert result == 'validation'


@behave.given(u'I have a single item with a subset assigned')
def step_impl(context):
    context.items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    context.single_item = context.items[1]
    context.single_item.assign_subset('test')



@behave.when(u'I remove the subset from the item')
def step_impl(context):
    context.single_item.remove_subset()


@behave.then(u'The item has no ML subset assigned')
def step_impl(context):
    context.single_item = context.dataset.items.get(item_id=context.single_item.id)
    result = context.single_item.get_current_subset()
    assert result is None


@behave.given(u'I have a single item with \'test\' subset assigned')
def step_impl(context):
    context.items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    context.single_item = context.items[2]
    context.single_item.assign_subset('test')
    assert context.single_item.get_current_subset() == 'test'


@behave.when(u'I get the current subset of the item')
def step_impl(context):
    context.current_subset = context.single_item.get_current_subset()


@behave.then(u'The result is \'test\'')
def step_impl(context):
    assert context.current_subset == 'test'


@behave.given(u'Some items in the dataset have subsets assigned and some do not')
def step_impl(context):
    context.items = list(context.dataset.items.list(filters=dl.Filters(field='type', values='file')).all())
    # Assign 'train' to first 2 items, leave others without subsets
    for item in context.items[:2]:
        item.assign_subset('train')
    # Others remain without subset


@behave.when(u'I get items missing ML subset')
def step_impl(context):
    context.missing_ids = context.dataset.get_items_missing_ml_subset()


@behave.then(u'I receive a list of item IDs with no ML subset assigned')
def step_impl(context):
    # The first 2 have train, others have None.
    assigned_ids = set(item.id for item in context.items[:2])
    missing_ids = set(item.id for item in context.items[2:])
    received_ids = set(context.missing_ids)
    assert received_ids == missing_ids
    assert received_ids and received_ids.isdisjoint(assigned_ids)
