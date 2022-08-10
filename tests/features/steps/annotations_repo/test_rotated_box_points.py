import behave
import numpy as np
import dtlpy as dl


@behave.given(u'I create 4ptBox setting to the "{project_num}" project')
def step_impl(context, project_num):
    if project_num == "first":
        context.project_4ptBox_settings = context.first_project.settings.create(setting_name='4ptBox', setting_value=True,
                                                                                setting_value_type=dl.SettingsValueTypes.BOOLEAN)
    else:
        context.project_4ptBox_settings = context.second_project.settings.create(setting_name='4ptBox', setting_value=True,
                                                                                 setting_value_type=dl.SettingsValueTypes.BOOLEAN)


@behave.given(u'I set 4ptBox setting project setting to "{settings_value}"')
def step_impl(context, settings_value):
    if settings_value == "False":
        context.first_project.settings.update(setting_name='4ptBox', setting_value=False,
                                              setting_id=context.project_4ptBox_settings.id)
    else:
        context.second_project.settings.update(setting_name='4ptBox', setting_value=True,
                                               setting_id=context.project_4ptBox_settings.id)


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
