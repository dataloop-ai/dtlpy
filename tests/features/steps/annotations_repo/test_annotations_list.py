import behave
import dtlpy as dl

@behave.given(u'There are no annotations')
def step_impl_no_annotations(context):
    assert True

@behave.when(u'I list all annotations')
def step_impl_list_all(context):
    context.annotations_list = context.item.annotations.list()

@behave.then(u'I receive a list of all annotations')
def step_impl_receive_all(context):
    assert len(context.annotations_list) == len(context.annotations), (
        f"Expected {len(context.annotations)} annotations, got {len(context.annotations_list)}"
    )

@behave.then(u'The annotations in the list equals the annotations uploaded')
def step_impl_compare_annotations(context):
    for annotation in context.annotations_list:
        ann = {
            'type': annotation.type,
            'label': annotation.label,
            'metadata': {'system': {'attributes': annotation.attributes}},
            'coordinates': annotation.coordinates
        }
        for coord in ann['coordinates']:
            coord.pop('z', None)
        assert ann in context.annotations, f"{ann} not found in uploaded annotations"

@behave.then(u'I receive an empty annotations list')
def step_impl_empty_list(context):
    assert len(context.annotations_list) == 0, (
        f"Expected 0 annotations, got {len(context.annotations_list)}"
    )

@behave.when(u'I list annotations with page_size {n:d}')
def step_list_with_page_size(context, n):
    filters = dl.Filters(resource=dl.FiltersResource.ANNOTATION)
    filters.page_size = n
    filters.page = 0
    filters.add(
        field='itemId',
        values=context.item.id,
        method=dl.FiltersMethod.AND
    )
    context.first_page = context.dataset.annotations.list(filters=filters)
    context.first_items = context.first_page.items
    context.last_seen_id = context.first_page.last_seen_id

@behave.when(u'I list annotations after last_seen_id with page_size {n:d}')
def step_list_after_cursor(context, n):
    filters = dl.Filters(resource=dl.FiltersResource.ANNOTATION)
    filters.page = 0
    filters.page_size = n
    filters.add(
        field="id",
        values=context.last_seen_id,
        operator=dl.FiltersOperations.GREATER_THAN,
        method=dl.FiltersMethod.AND
    )
    filters.add(
        field='itemId',
        values=context.item.id,
        method=dl.FiltersMethod.AND
    )
    context.second_page = context.dataset.annotations.list(filters=filters)
    context.second_items = list(context.second_page.items)
    assert context.second_items, "Second page has no annotations!"

@behave.then(u'that annotation’s id should not equal the first page’s id')
def step_assert_distinct_ids(context):
    first_id = context.first_items[0].id
    second_id = context.second_items[0].id
    assert second_id != first_id, \
        f"Second-page id {second_id} should differ from first-page id {first_id}"

@behave.then(u'I save the last_seen_id of that page')
def step_save_cursor(context):
    cursor = getattr(context.first_page, 'last_seen_id', None)
    assert cursor is not None, "Expected first_page.last_seen_id to be populated"
    context.last_seen_id = cursor
