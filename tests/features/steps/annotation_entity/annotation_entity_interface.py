import behave
import os


@behave.when(u'I call Annotation.download() using the given params')
def step_impl(context):
    context.filepath = None
    context.annotation_format = None
    context.height = None
    context.width = None
    context.thickness = 1
    context.with_text = False
    context.alpha = 1

    annotation_format_list = {
        "JSON": context.dl.VIEW_ANNOTATION_OPTIONS_JSON,
        "MASK": context.dl.VIEW_ANNOTATION_OPTIONS_MASK,
        "INSTANCE": context.dl.VIEW_ANNOTATION_OPTIONS_INSTANCE,
        "ANNOTATION_ON_IMAGE": context.dl.VIEW_ANNOTATION_OPTIONS_ANNOTATION_ON_IMAGE,
        "VTT": context.dl.VIEW_ANNOTATION_OPTIONS_VTT,
        "OBJECT_ID": context.dl.VIEW_ANNOTATION_OPTIONS_OBJECT_ID
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "filepath":
            context.filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "annotation_format":
            context.annotation_format = annotation_format_list[parameter.cells[1]]

        if parameter.cells[0] == "height":
            context.height = float(parameter.cells[1])

        if parameter.cells[0] == "width":
            context.width = float(parameter.cells[1])

        if parameter.cells[0] == "thickness":
            context.thickness = float(parameter.cells[1])

        if parameter.cells[0] == "with_text":
            context.with_text = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "alpha":
            context.alpha = float(parameter.cells[1])

    if context.annotation_format is None:
        context.annotation.download(
            filepath=context.filepath,
            height=context.height,
            width=context.width,
            thickness=context.thickness,
            with_text=context.with_text,
            alpha=context.alpha
        )
    else:
        context.annotation.download(
            filepath=context.filepath,
            annotation_format=context.annotation_format,
            height=context.height,
            width=context.width,
            thickness=context.thickness,
            with_text=context.with_text,
            alpha=context.alpha
        )


@behave.when(u'I update annotation attributes with params')
def step_impl(context):
    params = dict()
    for row in context.table:
        params[row['key']] = row['value']

    context.annotation.attributes = params
    context.annotation = context.annotation.update(True)


@behave.when(u'I update annotation attributes to empty dict')
def step_impl(context):
    context.annotation.attributes = {}
    context.annotation = context.annotation.update(True)


@behave.when(u'I update "{annotation_type}" annotation position on canvas')
def atp_step_impl(context, annotation_type):
    context.original_coordinates = []
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION, field='type', values=annotation_type)
    annotations = context.dataset.annotations.list(filters=filters)

    for annotation in annotations.items:
        if annotation.type == 'box':
            original_coords = {
                'left': annotation.left,
                'right': annotation.right,
                'top': annotation.top,
                'bottom': annotation.bottom
            }
            annotation.left += 10
            annotation.right += 10
            annotation.top += 10
            annotation.bottom += 10

        elif annotation.type == 'segment' or annotation.type == 'polyline':
            original_coords = {
                'x': list(annotation.annotation_definition.x),
                'y': list(annotation.annotation_definition.y)
            }
            x_coords = annotation.annotation_definition.x
            y_coords = annotation.annotation_definition.y
            for i in range(len(x_coords)):
                x_coords[i] += 10
                y_coords[i] += 10

        elif annotation.type == 'point':
            original_coords = {
                'x': annotation.annotation_definition.x,
                'y': annotation.annotation_definition.y
            }
            annotation.annotation_definition.x += 10
            annotation.annotation_definition.y += 10

        else:
            raise ValueError(f"Unsupported annotation type: {annotation.type}")

        context.original_coordinates.append(original_coords)
        annotation.update()


@behave.then(u'I validate that the "{annotation_type}" annotation position was changed')
def atp_step_impl(context, annotation_type):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION, field='type', values=annotation_type)
    annotations = context.dataset.annotations.list(filters=filters)

    for i, annotation in enumerate(annotations.items):
        original_coords = context.original_coordinates[i]
        if annotation.type == 'box':
            assert original_coords['left'] != annotation.left, "Box left coordinate did not change."
            assert original_coords['right'] != annotation.right, "Box right coordinate did not change."
            assert original_coords['top'] != annotation.top, "Box top coordinate did not change."
            assert original_coords['bottom'] != annotation.bottom, "Box bottom coordinate did not change."

        elif annotation.type == 'segment':
            for j, (x, y) in enumerate(zip(annotation.annotation_definition.x, annotation.annotation_definition.y)):
                assert original_coords['x'][j] != x, f"Segment x coordinate at index {j} did not change."
                assert original_coords['y'][j] != y, f"Segment y coordinate at index {j} did not change."

        elif annotation.type == 'point':
            assert original_coords['x'] != annotation.annotation_definition.x, "Point x coordinate did not change."
            assert original_coords['y'] != annotation.annotation_definition.y, "Point y coordinate did not change."


@behave.when(u'I sort annotations by "{field}" in "{order}" order')
def atp_step_impl(context, field, order):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION)

    # Determine the sorting direction
    if order.lower() == 'ascending':
        sort_order = context.dl.FiltersOrderByDirection.ASCENDING
    elif order.lower() == 'descending':
        sort_order = context.dl.FiltersOrderByDirection.DESCENDING
    else:
        raise ValueError(f"Invalid sorting order: {order}. Must be 'ascending' or 'descending'.")

    # Apply sorting by the specified field and order
    filters.sort_by(field=field, value=sort_order)

    # Fetch annotations with applied filters
    context.annotations = context.dataset.annotations.list(filters=filters)


@behave.then(u'I validate that annotations are sorted by "{field}" in "{order}" order')
def step_validate_sorted_annotations(context, field, order):
    annotations = context.annotations

    # Extract the relevant field values from annotations
    field_values = [getattr(annotation, field, None) for annotation in annotations]

    # Check sorting order
    if order.lower() == 'ascending':
        assert field_values == sorted(field_values), f"Annotations are not sorted by {field} in ascending order."
    elif order.lower() == 'descending':
        assert field_values == sorted(field_values,
                                      reverse=True), f"Annotations are not sorted by {field} in descending order."
    else:
        raise ValueError(f"Invalid sorting order: {order}")