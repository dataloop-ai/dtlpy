import behave
import os
import json


@behave.when(u'I call dataset.download_annotations() using the given params')
def step_impl(context):
    context.local_path = None
    # context.filters - Removed to prevent overwrite
    context.annotation_options = None
    context.annotation_filters = None
    context.overwrite = False
    context.thickness = 1
    context.with_text = False
    context.remote_path = None
    context.include_annotations_in_output = True
    context.export_png_files = False
    context.filter_output_annotations = False
    context.alpha = None
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

        if parameter.cells[0] == "filters":
            context.filters = context.dl.Filters(custom_filter=json.loads(parameter.cells[1]))

        if parameter.cells[0] == "annotation_options":
            context.annotation_options = annotation_options_list[parameter.cells[1]]

        if parameter.cells[0] == "annotation_filters":
            context.annotation_filters = context.dl.Filters(custom_filter=json.loads(parameter.cells[1]))

        if parameter.cells[0] == "overwrite":
            context.overwrite = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "thickness":
            context.thickness = float(parameter.cells[1])

        if parameter.cells[0] == "with_text":
            context.with_text = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "remote_path":
            context.remote_path = parameter.cells[1]

        if parameter.cells[0] == "include_annotations_in_output":
            context.include_annotations_in_output = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "export_png_files":
            context.export_png_files = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "filter_output_annotations":
            context.filter_output_annotations = True if parameter.cells[1] == "True" else False

        if parameter.cells[0] == "alpha":
            context.save_locally = float(parameter.cells[1])

        if parameter.cells[0] == "export_version":
            context.save_locally = export_versions_list[parameter.cells[1]]

    context.dataset.download_annotations(
        local_path=context.local_path,
        filters=context.filters,
        annotation_options=context.annotation_options,
        annotation_filters=context.annotation_filters,
        overwrite=context.overwrite,
        thickness=context.thickness,
        with_text=context.with_text,
        remote_path=context.remote_path,
        include_annotations_in_output=context.include_annotations_in_output,
        export_png_files=context.export_png_files,
        filter_output_annotations=context.filter_output_annotations,
        alpha=context.alpha,
        export_version=context.export_version
    )
