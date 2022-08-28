import os
import random
import time
import behave


@behave.when(u'I create two project  and datasets by the name of "{f_project_name}" "{s_project_name}"')
def creating_a_project(context, f_project_name, s_project_name):
    f_project_name = f_project_name + str(random.randint(10000, 100000))
    s_project_name = s_project_name + str(random.randint(10000, 100000))
    context.project = context.dl.projects.create(project_name=f_project_name)
    context.to_delete_projects_ids.append(context.project.id)
    context.second_project = context.dl.projects.create(project_name=s_project_name)
    context.to_delete_projects_ids.append(context.second_project.id)
    time.sleep(5)  # to sleep because authorization takes time
    context.first_dataset = context.project.datasets.create(dataset_name='f_project_name')
    context.second_dataset = context.second_project.datasets.create(dataset_name='s_project_name')


@behave.when(u'I upload item in "{item_path}" to both datasets')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.first_item = context.first_dataset.items.upload(local_path=item_path)
    context.second_item = context.second_dataset.items.upload(local_path=item_path)


@behave.when(u'i upload annotations to both items')
def step_impl(context):
    builder = context.first_item.annotations.builder()
    builder.add(annotation_definition=context.dl.Box(top=100, left=100, right=200, bottom=50, label='aa'))
    context.f_annotation = context.first_item.annotations.upload(builder)
    builder2 = context.second_item.annotations.builder()
    builder2.add(annotation_definition=context.dl.Box(top=100, left=100, right=200, bottom=50, label='aa'))
    context.s_annotation = context.second_item.annotations.upload(builder2)


@behave.when(u'add settings to the project')
def step_impl(context):
    context.setting = context.project.settings.create(setting_name='4ptBox', setting_value=True,
                                                      setting_value_type=context.dl.SettingsValueTypes.BOOLEAN)


@behave.then(u'check if geo in the first item and in the second are difference')
def step_impl(context):
    first_item_geo = context.f_annotation.annotations[0].geo
    second_item_geo = context.s_annotation.annotations[0].geo
    assert len(first_item_geo) == 4
    assert len(second_item_geo) == 2


@behave.when(u'I get setting by "{identifier}"')
def step_impl(context, identifier):
    if identifier == 'id':
        context.setting_get = context.project.settings.get(setting_id=context.setting.id)
    else:
        context.setting_get = context.project.settings.get(setting_name=context.setting.name)


@behave.then(u'I check setting got is equal to the one created')
def step_impl(context):
    assert context.setting_get.to_json() == context.setting.to_json()
