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
