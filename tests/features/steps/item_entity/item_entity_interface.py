import behave
import os
import json
from time import sleep


@behave.given(u'I call Item.download() using the given params')
def step_impl(context):
    context.local_path = None
    context.file_types = None
    context.save_locally = True
    context.to_array = False
    context.annotation_options = None
    context.overwrite = False
    context.to_items_folder = True
    context.thickness = 1
    context.with_text = False
    context.annotation_filters = None
    context.alpha = 1
    context.export_version = context.dl.ExportVersion.V1

    annotation_options_list = {
        "JSON": context.dl.VIEW_ANNOTATION_OPTIONS_JSON,
        "MASK": context.dl.VIEW_ANNOTATION_OPTIONS_MASK,
        "INSTANCE": context.dl.VIEW_ANNOTATION_OPTIONS_INSTANCE,
        "ANNOTATION_ON_IMAGE": context.dl.VIEW_ANNOTATION_OPTIONS_ANNOTATION_ON_IMAGE,
        "VTT": context.dl.VIEW_ANNOTATION_OPTIONS_VTT,
        "OBJECT_ID": context.dl.VIEW_ANNOTATION_OPTIONS_OBJECT_ID
    }

    export_versions_list = {
        "V1": context.dl.ExportVersion.V1,
        "V2": context.dl.ExportVersion.V2
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "local_path":
            context.local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "file_types":
            context.file_types = parameter.cells[1]

        if parameter.cells[0] == "save_locally":
            context.save_locally = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "to_array":
            context.to_array = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "annotation_options":
            context.annotation_options = annotation_options_list[parameter.cells[1]]

        if parameter.cells[0] == "overwrite":
            context.overwrite = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "to_items_folder":
            context.to_items_folder = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "thickness":
            context.thickness = float(parameter.cells[1])

        if parameter.cells[0] == "with_text":
            context.with_text = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "annotation_filters":
            context.annotation_filters = context.dl.Filters(custom_filter=json.loads(parameter.cells[1]))

        if parameter.cells[0] == "alpha":
            context.save_locally = float(parameter.cells[1])

        if parameter.cells[0] == "export_version":
            context.save_locally = export_versions_list[parameter.cells[1]]

    context.item.download(
        local_path=context.local_path,
        file_types=context.file_types,
        save_locally=context.save_locally,
        to_array=context.to_array,
        annotation_options=context.annotation_options,
        overwrite=context.overwrite,
        to_items_folder=context.to_items_folder,
        thickness=context.thickness,
        with_text=context.with_text,
        annotation_filters=context.annotation_filters,
        alpha=context.alpha,
        export_version=context.export_version
    )


@behave.when(u'I call Item.annotations.download() using the given params')
def step_impl(context):
    # Used to get item height and width from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    context.filepath = None
    context.annotation_format = None
    context.img_filepath = None
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

        if parameter.cells[0] == "img_filepath":
            context.img_filepath = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

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
        context.item.annotations.download(
            filepath=context.filepath,
            height=context.height,
            width=context.width,
            thickness=context.thickness,
            with_text=context.with_text,
            alpha=context.alpha
        )
    else:
        context.item.annotations.download(
            filepath=context.filepath,
            annotation_format=context.annotation_format,
            img_filepath=context.img_filepath,
            height=context.height,
            width=context.width,
            thickness=context.thickness,
            with_text=context.with_text,
            alpha=context.alpha
        )
