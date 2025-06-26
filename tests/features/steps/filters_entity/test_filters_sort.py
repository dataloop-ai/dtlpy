import os
import dtlpy as dl
from behave import given, when, then
from dateutil.parser import isoparse


# Reuse existing steps if possible by importing them
# If not, stub out new step definitions here

def _parse_date(field, value):
    if field in ['created_at', 'updated_at']:
        dt = isoparse(value) if value else None
        if dt is not None:
            return dt.replace(microsecond=0, second=0)
        return None
    return value


def _convert_field(field):
    if field in ['created_at', 'updated_at']:
      field = f"{field.split('_')[0]}{field.split('_')[1].capitalize()}"
    return field


@given('I create dataset and items for sorting tests')
def step_background_sorting(context):
    context.feature.called = 0 if not hasattr(context.feature, 'called') else 1
    if context.feature.called == 0:
        context.execute_steps(f"""
        Given I create a dataset with a random name
        And I upload an item in the path "images_numbers/1_50" to the dataset
        When I wait "60"
        Given I upload an item by the name of "img_51.jpg"
        When I upload labels to dataset
        And I upload "30" box annotation to item""")
    else:
        context.dataset = context.project.datasets.list()[0]
        context.item = context.dataset.items.get(filepath='/img_51.jpg')


@when('I list items sorted by {field} in {order} order')
def step_list_items_sorted(context, field, order):
    filters = dl.Filters()
    if order.lower() == 'ascending':
        sort_order = dl.FiltersOrderByDirection.ASCENDING
    elif order.lower() == 'descending':
        sort_order = dl.FiltersOrderByDirection.DESCENDING
    else:
        raise ValueError(f'Unknown order: {order}')
    field = _convert_field(field)
    filters.sort_by(field=field, value=sort_order)
    context.filtered_items_list = context.dataset.items.list(filters=filters)


@then('the items should be sorted by {field} in {order} order')
def step_verify_items_sorted(context, field, order):
    items_count = context.dataset.items.list().items_count
    items = context.filtered_items_list.items
    values = [_parse_date(field, getattr(item, field, None)) for item in items]

    # Validate values not empty list and has the correct amount of items
    assert values, f"Expected values , Actual: {values}"
    assert items_count == len(values), f"Dataset has {items_count} items , Sorted list returned {len(values)}"

    if order.lower() == 'ascending':
        assert values == sorted(values), f"Items not sorted by {field} ascending: {values}"
    elif order.lower() == 'descending':
        assert values == sorted(values, reverse=True), f"Items not sorted by {field} descending: {values}"
    else:
        raise ValueError(f'Unknown order: {order}')


@when('I list items sorted by {field} in {order} order with page size 10')
def step_list_items_sorted_paged(context, field, order):
    filters = dl.Filters()
    if order.lower() == 'ascending':
        sort_order = dl.FiltersOrderByDirection.ASCENDING
    elif order.lower() == 'descending':
        sort_order = dl.FiltersOrderByDirection.DESCENDING
    else:
        raise ValueError(f'Unknown order: {order}')

    field = _convert_field(field)
    filters.sort_by(field=field, value=sort_order)
    context.items_pages = context.dataset.items.list(filters=filters, page_size=10)


@then('the items across all pages should be sorted by {field} in {order} order')
def step_verify_items_sorted_paged(context, field, order):
    items_count = context.dataset.items.list().items_count
    values_amount = 0
    for page in context.items_pages:
        values = [_parse_date(field, getattr(item, field, None)) for item in page]

        # Validate values not empty list and has the correct amount of items
        assert values, f"Expected values , Actual: {values}"

        if order.lower() == 'ascending':
            assert values == sorted(values), f"Paged items not sorted by {field} ascending: {values}"
        elif order.lower() == 'descending':
            assert values == sorted(values, reverse=True), f"Paged items not sorted by {field} descending: {values}"
        else:
            raise ValueError(f'Unknown order: {order}')

        values_amount += len(values)
    # Validate values has the correct amount of items
    assert items_count == values_amount, f"Dataset has {items_count} items , Sorted list returned {len(values)}"


@when('I list annotations sorted by {field} in {order} order')
def step_list_annotations_sorted(context, field, order):
    filters = dl.Filters(resource=dl.FiltersResource.ANNOTATION)
    if order.lower() == 'ascending':
        sort_order = dl.FiltersOrderByDirection.ASCENDING
    elif order.lower() == 'descending':
        sort_order = dl.FiltersOrderByDirection.DESCENDING
    else:
        raise ValueError(f'Unknown order: {order}')

    field = _convert_field(field)
    filters.sort_by(field=field, value=sort_order)
    context.filtered_annotations_list = context.dataset.annotations.list(filters=filters)


@then('the annotations should be sorted by {field} in {order} order')
def step_verify_annotations_sorted(context, field, order):
    annotations = context.filtered_annotations_list.items
    annotations_count = context.dataset.annotations.list().items_count
    values = [_parse_date(field, getattr(ann, field, None)) for ann in annotations]

    # Validate values not empty list and has the correct amount of annotations
    assert values, f"Expected values , Actual: {values}"
    assert annotations_count == len(values), f"Dataset has {annotations_count} annotations , Sorted list returned {len(values)}"

    if order.lower() == 'ascending':
        assert values == sorted(values), f"Annotations not sorted by {field} ascending: {values}"
    elif order.lower() == 'descending':
        assert values == sorted(values, reverse=True), f"Annotations not sorted by {field} descending: {values}"
    else:
        raise ValueError(f'Unknown order: {order}')


@when('I list annotations sorted by {field} in {order} order with page size 10')
def step_list_annotations_sorted_paged(context, field, order):
    filters = dl.Filters(resource=dl.FiltersResource.ANNOTATION)
    if order.lower() == 'ascending':
        sort_order = dl.FiltersOrderByDirection.ASCENDING
    elif order.lower() == 'descending':
        sort_order = dl.FiltersOrderByDirection.DESCENDING
    else:
        raise ValueError(f'Unknown order: {order}')
    field = _convert_field(field)
    filters.sort_by(field=field, value=sort_order)
    filters.page_size = 10
    context.paged_annotations = []
    context.annotations_page = context.dataset.annotations.list(filters=filters)


@then('the annotations across all pages should be sorted by {field} in {order} order')
def step_verify_annotations_sorted_paged(context, field, order):
    annotations_count = context.dataset.annotations.list().items_count
    values_amount = 0
    for page in context.annotations_page:
        values = [_parse_date(field, getattr(ann, field, None)) for ann in page]

        # Validate values not empty list
        assert values, f"Expected values , Actual: {values}"
        if order.lower() == 'ascending':
            assert values == sorted(values), f"Paged annotations not sorted by {field} ascending: {values}"
        elif order.lower() == 'descending':
            assert values == sorted(values, reverse=True), f"Paged annotations not sorted by {field} descending: {values}"
        else:
            raise ValueError(f'Unknown order: {order}')

        values_amount += len(values)
    # Validate values has the correct amount of annotations
    assert annotations_count == values_amount, f"Dataset has {annotations_count} annotations , Sorted list returned {len(values)}"
