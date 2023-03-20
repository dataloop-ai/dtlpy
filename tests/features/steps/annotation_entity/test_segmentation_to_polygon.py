import behave
import os
import numpy as np


@behave.when(u'I call Polygon.from_segmentation() using "{max_instances}" nax_instances')
def step_impl(context, max_instances):
    polygon = context.dl.Polygon.from_segmentation(context.annotation.annotation_definition.geo,
                                                   context.annotation.label,
                                                   max_instances=int(max_instances))
    builder = context.item.annotations.builder()
    builder.add(annotation_definition=polygon)
    annotations = builder.upload().annotations
    context.polygons = annotations


@behave.then(u'The polygon will match to the json file "{json_file_path}"')
def step_impl(context, json_file_path):
    polygons_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], json_file_path)
    annotations = context.item.annotations.upload(polygons_path).annotations

    for i in range(len(annotations)):
        assert np.array_equal(context.polygons[i].geo, annotations[i].geo)
