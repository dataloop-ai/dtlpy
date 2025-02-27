import behave
import numpy as np
import dtlpy as dl

@behave.when(u'I upload rotated box annotation to item "{item_num}"')
def step_impl(context, item_num):
    if item_num == "1":
        builder = context.first_item.annotations.builder()
        builder.add(annotation_definition=dl.Box(top=10, left=10, bottom=100, right=100, label='test', angle=80))
        context.first_item.annotations.upload(builder)
        context.rotated_box_geo = builder.annotations[0].geo
    else:
        builder = context.second_item.annotations.builder()
        builder.add(annotation_definition=dl.Box(top=10, left=10, bottom=100, right=100, label='test', angle=80))
        context.second_item.annotations.upload(builder)
        context.rotated_box_geo = builder.annotations[0].geo


@behave.then(u'The Geo will be of the "{format_type}" format')
def step_impl(context, format_type):
    if format_type == 'old':
        old_format = np.array([[10, 10],
                               [100, 100]])
        assert np.array_equal(context.rotated_box_geo, old_format)
    else:
        new_format = np.array([[91.0, 2.0],
                               [2.0, 18.0],
                               [18.0, 107.0],
                               [107.0, 91.0]])
        assert np.array_equal(np.floor(context.rotated_box_geo), new_format)
